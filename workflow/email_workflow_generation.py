import logging

logger = logging.getLogger(__name__)


def create_email_workflow_job():
    """
    Scheduled job placeholder for email-to-workflow ingestion.
    Extend this to poll IMAP and create EmailWorkFlow / WorkflowInstance records.
    """
    logger.debug("Email workflow job tick (no-op in boilerplate)")
