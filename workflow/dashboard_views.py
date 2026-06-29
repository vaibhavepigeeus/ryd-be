import logging
from datetime import datetime
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from users.models import Users
from .models import WorkflowInstance
from .serializers import NotificationSerializer

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_workflow_dashboard_summary(request):
    """
    Returns workflow metrics: Total Workflows, In Process, Completed, Overdue, Rejected
    from workflow_workflowbanktransactions table
    """
    try:
        # Get filter parameters from query string
        workflow_name = request.query_params.get('workflow_name', '').strip()
        date_from = request.query_params.get('date_from', '').strip()
        date_to = request.query_params.get('date_to', '').strip()
        initiated_by = request.query_params.get('initiated_by', '').strip()
        status_filter = request.query_params.get('status', '').strip()
        transaction_id = request.query_params.get('transaction_id', '').strip()
        
        # Build filter query - start with all workflows
        filter_conditions = Q()
        
        # Apply filters only if provided
        if workflow_name:
            # Filter by workflow name if workflow relationship exists
            # Only filter if workflow is not None
            # Use exact match or icontains for partial match
            filter_conditions &= Q(workflow__isnull=False) & (
                Q(workflow__workflow_name__iexact=workflow_name) | 
                Q(workflow__workflow_name__icontains=workflow_name)
            )
        
        if transaction_id:
            # Filter by transaction ID (bank_txn_id)
            filter_conditions &= Q(bank_txn_id__icontains=transaction_id)
        
        if date_from:
            try:
                # Handle different date formats
                if len(date_from) == 10:  # YYYY-MM-DD
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                else:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__gte=date_from_obj)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid date_from format: {date_from}, error: {e}")
        
        if date_to:
            try:
                if len(date_to) == 10:  # YYYY-MM-DD
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                else:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__lte=date_to_obj)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid date_to format: {date_to}, error: {e}")
        
        if status_filter:
            filter_conditions &= Q(workflow_status__iexact=status_filter)
        
        # Get all workflow bank transactions matching filters
        try:
            if filter_conditions:
                workflows = WorkflowInstance.objects.filter(filter_conditions)
            else:
                workflows = WorkflowInstance.objects.all()
        except Exception as e:
            logger.error(f"Error querying WorkflowInstance: {e}")
            # Return empty metrics if query fails
            return Response({
                "totalWorkflows": 0,
                "inProcess": 0,
                "completed": 0,
                "rejected": 0,
                "overdue": 0
            }, status=status.HTTP_200_OK)
        
        # Filter by initiated_by if provided (search in workflow_json_data)
        if initiated_by:
            filtered_workflows = []
            for wf in workflows:
                try:
                    workflow_json = wf.workflow_json_data or {}
                    workflow_steps = workflow_json.get('workflow_step', [])
                    # Check if any step has a user with matching user_name
                    for step in workflow_steps:
                        users = step.get('user', [])
                        for user in users:
                            user_name = user.get('user_name', '')
                            if user_name and initiated_by.lower() in user_name.lower():
                                filtered_workflows.append(wf)
                                break
                        if wf in filtered_workflows:
                            break
                except Exception as e:
                    logger.warning(f"Error checking initiated_by for workflow {wf.id}: {e}")
                    continue
            workflows = WorkflowInstance.objects.filter(id__in=[wf.id for wf in filtered_workflows])
        
        # Initialize metrics
        metrics = {
            "totalWorkflows": 0,
            "inProcess": 0,
            "completed": 0,
            "rejected": 0,
            "overdue": 0
        }
        
        # Get current time in UTC
        now = timezone.now()
        overdue_days = 5  # Threshold for overdue
        
        total_count = workflows.count()
        metrics["totalWorkflows"] = total_count
        
        if total_count == 0:
            return Response(metrics, status=status.HTTP_200_OK)
        
        # Count by status and calculate overdue
        for workflow in workflows:
            try:
                status_value = workflow.workflow_status
                if status_value:
                    status_lower = str(status_value).strip().lower()
                    
                    # Count basic statuses
                    if status_lower == "completed":
                        metrics["completed"] += 1
                    elif status_lower in ["in process", "in_process"]:
                        metrics["inProcess"] += 1
                    elif status_lower == "rejected":
                        metrics["rejected"] += 1
                
                # Calculate Overdue
                # Check if it's not completed and has been open longer than the threshold
                if status_value and str(status_value).strip().lower() != "completed":
                    if workflow.created_at:
                        try:
                            # Calculate days open
                            days_open = (now - workflow.created_at).days
                            
                            if days_open > overdue_days:
                                metrics["overdue"] += 1
                        except Exception as e:
                            logger.error(f"Error calculating days for workflow {workflow.id}: {e}")
            except Exception as e:
                logger.error(f"Error processing workflow {workflow.id}: {e}")
                continue
        
        return Response(metrics, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_workflow_dashboard_summary: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return error details for debugging
        error_details = {
            'error': str(e),
            'message': 'Failed to fetch workflow dashboard summary',
            'type': type(e).__name__
        }
        logger.error(f"Full error details: {error_details}")
        return Response(
            error_details, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
def get_aging_analysis(request):
    """
    Returns aging analysis data for workflows grouped by age buckets
    """
    print(">>> [LOG] Starting get_aging_analysis API")
    try:
        # Get filter parameters from query string
        workflow_name = request.query_params.get('workflow_name', '').strip()
        date_from = request.query_params.get('date_from', '').strip()
        date_to = request.query_params.get('date_to', '').strip()
        status_filter = request.query_params.get('status', '').strip()
        transaction_id = request.query_params.get('transaction_id', '').strip()
        initiated_by = request.query_params.get('initiated_by', '').strip()
        print(f">>> [LOG] Filters - Name: {workflow_name}, From: {date_from}, To: {date_to}, Status: {status_filter}, TxnID: {transaction_id}, InitiatedBy: {initiated_by}")
        
        # Build filter query
        filter_conditions = Q()
        
        # Exclude completed workflows for aging analysis
        filter_conditions &= ~Q(workflow_status__iexact='completed')
        print(">>> [LOG] Added condition: Exclude 'completed' status")
        
        if workflow_name:
            filter_conditions &= Q(workflow__isnull=False) & Q(workflow__workflow_name__icontains=workflow_name)
            print(f">>> [LOG] Added Name Filter for: {workflow_name}")
        
        if transaction_id:
            filter_conditions &= Q(bank_txn_id__icontains=transaction_id)
            print(f">>> [LOG] Added Transaction ID Filter: {transaction_id}")
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date() if len(date_from) == 10 else datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__gte=date_from_obj)
                print(f">>> [LOG] Added Date From Filter: {date_from_obj}")
            except Exception as e:
                print(f">>> [LOG] Date From Parsing Error: {e}")
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date() if len(date_to) == 10 else datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__lte=date_to_obj)
                print(f">>> [LOG] Added Date To Filter: {date_to_obj}")
            except Exception as e:
                print(f">>> [LOG] Date To Parsing Error: {e}")
        
        if status_filter:
            filter_conditions &= Q(workflow_status__iexact=status_filter)
            print(f">>> [LOG] Added Status Filter: {status_filter}")
        
        # Fetch workflows
        try:
            workflows = WorkflowInstance.objects.filter(filter_conditions)
            count_found = workflows.count()
            print(f">>> [LOG] Database query executed. Found {count_found} active workflows to analyze.")
        except Exception as e:
            print(f">>> [LOG] DATABASE QUERY ERROR: {e}")
            return Response({"labels": ["0-5 Days", "6-10 Days", "11-20 Days", "> 20 Days"], "counts": [0, 0, 0, 0]}, status=status.HTTP_200_OK)
        
        # Initialize our buckets
        aging_data = {"0-5 Days": 0, "6-10 Days": 0, "11-20 Days": 0, "> 20 Days": 0}
        now = timezone.now()
        print(f">>> [LOG] Current Time (UTC): {now}")

        # Processing loop
        for wf in workflows:
            if wf.created_at:
                try:
                    diff = (now - wf.created_at).days
                    # print(f">>> [LOG] Workflow ID {wf.id} age: {diff} days") # Un-comment for very deep debugging
                    
                    if diff <= 5:
                        aging_data["0-5 Days"] += 1
                    elif 6 <= diff <= 10:
                        aging_data["6-10 Days"] += 1
                    elif 11 <= diff <= 20:
                        aging_data["11-20 Days"] += 1
                    else:
                        aging_data["> 20 Days"] += 1
                except Exception as e:
                    print(f">>> [LOG] Math error on row {wf.id}: {e}")

        response_data = {
            "labels": list(aging_data.keys()),
            "counts": list(aging_data.values())
        }
        print(f">>> [LOG] Final Aging Distribution: {response_data['counts']}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f">>> [LOG] CRITICAL API ERROR: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_workflow_type_breakdown(request):
    print(">>> [LOG] Starting get_workflow_type_breakdown API")
    try:
        # Get filter parameters
        workflow_name = request.query_params.get('workflow_name', '').strip()
        date_from = request.query_params.get('date_from', '').strip()
        date_to = request.query_params.get('date_to', '').strip()
        transaction_id = request.query_params.get('transaction_id', '').strip()
        status_filter = request.query_params.get('status', '').strip()
        initiated_by = request.query_params.get('initiated_by', '').strip()
        print(f">>> [LOG] Received filters - Name: {workflow_name}, From: {date_from}, To: {date_to}, TxnID: {transaction_id}, Status: {status_filter}, InitiatedBy: {initiated_by}")

        # 1. Start with the base query of all transactions
        queryset = WorkflowInstance.objects.all()
        print(f">>> [LOG] Initial transaction count: {queryset.count()}")

        # 2. Apply filters to the transactions (Table 1)
        filter_conditions = Q()
        if workflow_name:
            filter_conditions &= Q(workflow__isnull=False) & Q(workflow__workflow_name__icontains=workflow_name)
        if transaction_id:
            filter_conditions &= Q(bank_txn_id__icontains=transaction_id)
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date() if len(date_from) == 10 else datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__gte=date_from_obj)
            except Exception as e:
                print(f">>> [LOG] Date From Parsing Error: {e}")
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date() if len(date_to) == 10 else datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__lte=date_to_obj)
            except Exception as e:
                print(f">>> [LOG] Date To Parsing Error: {e}")
        if status_filter:
            filter_conditions &= Q(workflow_status__iexact=status_filter)
        
        filtered_queryset = queryset.filter(filter_conditions)
        print(f">>> [LOG] Transactions after filtering: {filtered_queryset.count()}")
        
        # Filter by initiated_by if provided (search in workflow_json_data)
        if initiated_by:
            filtered_workflows = []
            for wf in filtered_queryset:
                try:
                    workflow_json = wf.workflow_json_data or {}
                    workflow_steps = workflow_json.get('workflow_step', [])
                    # Check if any step has a user with matching user_name
                    for step in workflow_steps:
                        users = step.get('user', [])
                        for user in users:
                            user_name = user.get('user_name', '')
                            if user_name and initiated_by.lower() in user_name.lower():
                                filtered_workflows.append(wf)
                                break
                        if wf in filtered_workflows:
                            break
                except Exception as e:
                    logger.warning(f"Error checking initiated_by for workflow {wf.id}: {e}")
                    continue
            filtered_queryset = WorkflowInstance.objects.filter(id__in=[wf.id for wf in filtered_workflows])
            print(f">>> [LOG] After initiated_by filter: {filtered_queryset.count()} workflows")

        # 3. Perform the Aggregation (The "Group By" logic)
        # This joins Table 1 and Table 2 to count occurrences of each workflow name
        breakdown = (
            filtered_queryset
            .values('workflow__workflow_name')  # Group by the name from Table 2
            .annotate(total=Count('id'))        # Count the IDs from Table 1
            .order_by('-total')                 # Sort by highest count first
        )
        print(f">>> [LOG] Raw aggregation result: {list(breakdown)}")

        # 4. Format the data for the UI
        # UI expects: [{ name: "WORKFLOW_NAME", value: 10 }, ...]
        formatted_data = [
            {
                "name": item['workflow__workflow_name'] if item['workflow__workflow_name'] else "Unknown",
                "value": item['total']
            } 
            for item in breakdown
        ]
        print(f">>> [LOG] Final formatted data sent to UI: {formatted_data}")

        return Response(formatted_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f">>> [LOG] ERROR: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_workflow_overview(request):
    print(">>> [LOG] Starting get_workflow_overview API")
    try:
        # 1. Fetch all Workflow Types from Table 2
        workflow_types = WorkFlow.objects.all()
        print(f">>> [LOG] Found {workflow_types.count()} workflow types in Table 2")

        now = timezone.now()
        overdue_threshold = 5  # Days
        overview_data = []

        # 2. For each type, calculate stats from Table 1
        for wf_type in workflow_types:
            print(f">>> [LOG] Processing Type: {wf_type.workflow_name}")

            # Get all transactions of this specific type
            related_txns = WorkflowInstance.objects.filter(workflow=wf_type)
            total_count = related_txns.count()
            
            if total_count == 0:
                continue # Skip types with no data

            # Calculate In Progress vs Completed vs Rejected
            completed_count = related_txns.filter(workflow_status__iexact='completed').count()
            in_process_count = related_txns.filter(workflow_status__iexact='in process').count()
            rejected_count = related_txns.filter(workflow_status__iexact='rejected').count()
            
            # Calculate Overdue (Only in process workflows that are older than threshold days)
            # Exclude completed and rejected workflows from overdue calculation
            overdue_count = related_txns.filter(
                workflow_status__iexact='in process',
                created_at__lte=now - timedelta(days=overdue_threshold)
            ).count()

            # Calculate Average Age (for active workflows)
            active_txns = related_txns.exclude(workflow_status__iexact='completed')
            total_age = 0
            avg_age = 0
            if active_txns.exists():
                for txn in active_txns:
                    total_age += (now - txn.created_at).days
                avg_age = total_age // active_txns.count()

            # Determine UI Status logic
            ui_status = "On Track"
            if overdue_count > 0:
                ui_status = "At Risk"
            if overdue_count > (total_count * 0.2): # More than 20% overdue
                ui_status = "Delayed"

            # 3. Append formatted object to list
            overview_data.append({
                "workflowType": wf_type.workflow_name,
                "inProgress": {
                    "completed": int((completed_count / total_count) * 100) if total_count > 0 else 0,
                    "remaining": int((in_process_count / total_count) * 100) if total_count > 0 else 0,
                    "rejected": int((rejected_count / total_count) * 100) if total_count > 0 else 0,
                    "completedCount": completed_count,
                    "inProcessCount": in_process_count,
                    "rejectedCount": rejected_count,
                    "totalCount": total_count
                },
                "overdue": overdue_count,
                "avgAge": f"{avg_age} Days",
                "status": ui_status
            })

        print(f">>> [LOG] Final Overview Data: {overview_data}")
        return Response(overview_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f">>> [LOG] ERROR: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_team_activity(request):
    print(">>> [LOG] Starting get_team_activity API")
    try:
        # Get filter parameters from query string
        workflow_name = request.query_params.get('workflow_name', '').strip()
        date_from = request.query_params.get('date_from', '').strip()
        date_to = request.query_params.get('date_to', '').strip()
        status_filter = request.query_params.get('status', '').strip()
        transaction_id = request.query_params.get('transaction_id', '').strip()
        initiated_by = request.query_params.get('initiated_by', '').strip()
        print(f">>> [LOG] Filters - Name: {workflow_name}, From: {date_from}, To: {date_to}, Status: {status_filter}, TxnID: {transaction_id}, InitiatedBy: {initiated_by}")
        
        # Build filter query
        filter_conditions = Q()
        
        # 1. Fetch only workflows that are currently "in process"
        filter_conditions &= Q(workflow_status__iexact='in process')
        
        # Apply additional filters
        if workflow_name:
            filter_conditions &= Q(workflow__isnull=False) & Q(workflow__workflow_name__icontains=workflow_name)
            print(f">>> [LOG] Added Name Filter for: {workflow_name}")
        
        if transaction_id:
            filter_conditions &= Q(bank_txn_id__icontains=transaction_id)
            print(f">>> [LOG] Added Transaction ID Filter: {transaction_id}")
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date() if len(date_from) == 10 else datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__gte=date_from_obj)
                print(f">>> [LOG] Added Date From Filter: {date_from_obj}")
            except Exception as e:
                print(f">>> [LOG] Date From Parsing Error: {e}")
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date() if len(date_to) == 10 else datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__lte=date_to_obj)
                print(f">>> [LOG] Added Date To Filter: {date_to_obj}")
            except Exception as e:
                print(f">>> [LOG] Date To Parsing Error: {e}")
        
        if status_filter:
            filter_conditions &= Q(workflow_status__iexact=status_filter)
            print(f">>> [LOG] Added Status Filter: {status_filter}")
        
        # Fetch workflows with filters
        active_workflows = WorkflowInstance.objects.filter(filter_conditions)
        
        # Filter by initiated_by if provided (search in workflow_json_data)
        if initiated_by:
            filtered_workflows = []
            for wf in active_workflows:
                try:
                    workflow_json = wf.workflow_json_data or {}
                    workflow_steps = workflow_json.get('workflow_step', [])
                    # Check if any step has a user with matching user_name
                    for step in workflow_steps:
                        users = step.get('user', [])
                        for user in users:
                            user_name = user.get('user_name', '')
                            if user_name and initiated_by.lower() in user_name.lower():
                                filtered_workflows.append(wf)
                                break
                        if wf in filtered_workflows:
                            break
                except Exception as e:
                    logger.warning(f"Error checking initiated_by for workflow {wf.id}: {e}")
                    continue
            active_workflows = WorkflowInstance.objects.filter(id__in=[wf.id for wf in filtered_workflows])
        
        print(f">>> [LOG] Found {active_workflows.count()} active workflows after filtering")
        
        # This dictionary will store: { "User Name": {"assigned": X, "overdue": Y, "workflows": set()} }
        # Using a set to track unique workflows per user to ensure each workflow is counted only once per user
        user_stats = {}
        now = timezone.now()
        overdue_threshold = 5

        for wf in active_workflows:
            # 2. Parse the JSON audit trail
            # Based on your data, the JSON is in the second column (index 1)
            steps = wf.workflow_json_data.get('workflow_step', [])
            
            # 3. Find the FIRST step that is currently pending (status is null or empty)
            # Only count the current active step, not all pending steps
            current_step_found = False
            for step in steps:
                if not step.get('status') and not current_step_found:  # This is the current holder of the task
                    users = step.get('user', [])
                    current_step_found = True  # Only process the first pending step
                    
                    # Track which users are assigned to this workflow's current step
                    assigned_users = set()
                    for user in users:
                        name = user.get('user_name', 'Unknown')
                        assigned_users.add(name)
                    
                    # Count this workflow once for each assigned user (if not already counted)
                    for name in assigned_users:
                        # Initialize user in our dictionary if not present
                        if name not in user_stats:
                            user_stats[name] = {
                                "tasksAssigned": 0, 
                                "tasksOverdue": 0,
                                "workflows": set()  # Track unique workflows for this user
                            }
                        
                        # Only count this workflow once per user (even if user appears multiple times in step)
                        if wf.id not in user_stats[name]["workflows"]:
                            user_stats[name]["workflows"].add(wf.id)
                            user_stats[name]["tasksAssigned"] += 1
                            
                            # Check if THIS specific task is overdue for THIS user
                            if wf.created_at and (now - wf.created_at).days > overdue_threshold:
                                user_stats[name]["tasksOverdue"] += 1
                    
                    # Break after processing the first pending step
                    break
        
        # 5. Format for the UI Table
        formatted_data = [
            {
                "teamMember": name,
                "tasksAssigned": stats["tasksAssigned"],
                "tasksOverdue": stats["tasksOverdue"]
            }
            for name, stats in user_stats.items()
        ]
        
        print(f">>> [LOG] Final Team Activity Data: {formatted_data}")
        return Response(formatted_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f">>> [LOG] ERROR: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_pending_workflow_details(request):
    print(">>> [LOG] Starting get_pending_workflow_details API")
    try:
        # Get filter parameters from query string
        workflow_name = request.query_params.get('workflow_name', '').strip()
        date_from = request.query_params.get('date_from', '').strip()
        date_to = request.query_params.get('date_to', '').strip()
        initiated_by = request.query_params.get('initiated_by', '').strip()
        status_filter = request.query_params.get('status', '').strip()
        transaction_id = request.query_params.get('transaction_id', '').strip()
        
        # Build filter query - default to pending/in process workflows unless status filter is provided
        if status_filter:
            filter_conditions = Q(workflow_status__iexact=status_filter)
        else:
            filter_conditions = Q(workflow_status__iexact='in process')
        
        # Apply filters only if provided
        if workflow_name:
            filter_conditions &= Q(workflow__isnull=False) & Q(workflow__workflow_name__icontains=workflow_name)
        
        if transaction_id:
            filter_conditions &= Q(bank_txn_id__icontains=transaction_id)
        
        if date_from:
            try:
                if len(date_from) == 10:  # YYYY-MM-DD
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                else:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__gte=date_from_obj)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid date_from format: {date_from}, error: {e}")
        
        if date_to:
            try:
                if len(date_to) == 10:  # YYYY-MM-DD
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                else:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S').date()
                filter_conditions &= Q(created_at__date__lte=date_to_obj)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid date_to format: {date_to}, error: {e}")
        
        # Get pending workflows
        pending_workflows = WorkflowInstance.objects.filter(filter_conditions).select_related('workflow').order_by('-created_at')[:50]  # Limit to 50 most recent
        
        now = timezone.now()
        formatted_data = []
        
        for wf in pending_workflows:
            # Calculate age in days
            age_days = 0
            if wf.created_at:
                age_days = (now - wf.created_at).days
            
            # Get workflow type name
            workflow_type = wf.workflow.workflow_name if wf.workflow else "Unknown"
            
            # Get current step
            current_step = wf.current_step if wf.current_step else "N/A"
            
            # Get transaction ID
            transaction_id = wf.bank_txn_id if wf.bank_txn_id else f"WF-{wf.id}"
            
            formatted_data.append({
                "transactionId": transaction_id,
                "workflowType": workflow_type,
                "currentStep": current_step,
                "age": f"{age_days} Days"
            })
        
        print(f">>> [LOG] Final Pending Workflow Details Data: {len(formatted_data)} records")
        return Response(formatted_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f">>> [LOG] ERROR: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
