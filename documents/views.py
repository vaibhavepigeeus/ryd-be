from datetime import datetime
from urllib.parse import unquote

from decouple import config
from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from backend.storage_backends import create_presigned_url
from .email import read_emails, send_email as send_reply
from .models import Documents, Entity
from .serializers import DocumentsSerializer, EntitySerializer


class CountModelMixin:
    @action(detail=False)
    def count(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response({"count": queryset.count()})


class DocumentsViewSet(viewsets.ModelViewSet, CountModelMixin):
    queryset = Documents.objects.all()
    serializer_class = DocumentsSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def _resolve_document_file(self, data, request=None):
        doc_files = data.get("document_file")
        if not doc_files:
            return data

        doc_file = str(doc_files)
        use_s3 = config("USE_S3", default=False, cast=bool)

        if use_s3 and doc_file.startswith("http"):
            bucket = config("AWS_STORAGE_BUCKET_NAME", default="")
            bucket_key = doc_file.replace(f"https://{bucket}.s3.amazonaws.com/", "")
            data["document_file"] = create_presigned_url(bucket, bucket_key) or doc_file
        elif request is not None:
            if doc_file.startswith("http"):
                data["document_file"] = doc_file
            elif doc_file.startswith("/"):
                data["document_file"] = request.build_absolute_uri(doc_file)
            else:
                from django.conf import settings as django_settings

                data["document_file"] = request.build_absolute_uri(
                    django_settings.MEDIA_URL + doc_file
                )

        return data

    def _presign_document_file(self, data, request=None):
        return self._resolve_document_file(data, request)

    def list(self, request):
        serializer = DocumentsSerializer(Documents.objects.all(), many=True)
        data = [self._presign_document_file(item, request) for item in serializer.data]
        return Response(data)

    def retrieve(self, request, pk=None):
        doc = Documents.objects.get(id=pk)
        data = self._presign_document_file(DocumentsSerializer(doc).data, request)
        return Response(data)

    def create(self, request, *args, **kwargs):
        data = request.data
        new_doc = Documents.objects.create(
            document_name=data["document_name"],
            document_date=data["document_date"],
            upload_date=datetime.now(),
            document_type=data["document_type"],
        )
        if data.get("document_file"):
            new_doc.document_file = data["document_file"]
            new_doc.save()
        response_data = self._presign_document_file(
            DocumentsSerializer(new_doc).data,
            request,
        )
        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        doc_object = self.get_object()
        data = request.data
        doc_object.document_name = data["document_name"]
        doc_object.document_date = data["document_date"]
        doc_object.upload_date = data.get("upload_date", doc_object.upload_date)
        doc_object.document_file = data.get("document_file", doc_object.document_file)
        doc_object.document_type = data["document_type"]
        doc_object.save()
        return Response(self._presign_document_file(DocumentsSerializer(doc_object).data, request))

    def partial_update(self, request, *args, **kwargs):
        doc_object = self.get_object()
        data = request.data
        for field in ["document_name", "document_date", "upload_date", "document_file", "document_type"]:
            if field in data:
                setattr(doc_object, field, data[field])
        doc_object.save()
        return Response(self._presign_document_file(DocumentsSerializer(doc_object).data, request))

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response({"message": "documents deleted successfully"})


class EntityViewSet(viewsets.ModelViewSet):
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer


@api_view(["GET"])
def read_email_list(request):
    try:
        from_date_str = request.query_params.get("fromDate")
        to_date_str = request.query_params.get("toDate")
        from_name = request.query_params.get("fromName")
        if from_date_str:
            from_date_str = unquote(from_date_str)
        if to_date_str:
            to_date_str = unquote(to_date_str)
        if from_name:
            from_name = unquote(from_name)

        page_index = int(request.query_params.get("skip", 0))
        page_size = int(request.query_params.get("pageSize", 25))
        emails = read_emails(from_date_str=from_date_str, to_date_str=to_date_str, from_name=from_name) or []
        total_count = len(emails)
        start = page_index * page_size
        end = start + page_size
        return Response({"data": emails[start:end], "count": total_count}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def send_reply_email(request):
    try:
        return Response({"data": send_reply(request.data)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def get_all_entity_divisions(request):
    divisions = Entity.objects.values_list("entity_divisions", flat=True).distinct()
    return Response({"data": list(divisions)})
