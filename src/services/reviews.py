from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models import Review, ActionItem, Project, AuditLog
from src.logger import logger

def add_review(
    db: Session,
    project_id: int,
    review_date: date,
    rubric_scores: Dict[str, Any],
    attendance: float = 1.0,
    reviewer_comment: str = "",
    action_items_summary: str = "",
    action_items_list: Optional[List[Dict[str, Any]]] = None,
    creator_id: Optional[int] = None
) -> Review:
    """Creates a project review along with explicit action items."""
    review = Review(
        project_id=project_id,
        review_date=review_date,
        rubric_scores=rubric_scores,
        attendance=attendance,
        reviewer_comment=reviewer_comment.strip() if reviewer_comment else "",
        action_items_summary=action_items_summary.strip() if action_items_summary else ""
    )
    db.add(review)
    db.flush()

    if action_items_list:
        for item in action_items_list:
            ai = ActionItem(
                review_id=review.id,
                project_id=project_id,
                description=item.get("description", "").strip(),
                due_date=item.get("due_date", review_date),
                status=item.get("status", "pending")
            )
            db.add(ai)

    # Audit log
    audit = AuditLog(
        user_id=creator_id,
        action="ADD_REVIEW",
        details={"review_id": review.id, "project_id": project_id, "score": rubric_scores}
    )
    db.add(audit)
    db.commit()
    db.refresh(review)
    logger.info(f"Added review {review.id} for project {project_id}")
    return review

def update_action_item_status(db: Session, item_id: int, status: str, user_id: Optional[int] = None) -> ActionItem:
    """Updates action item status: pending, completed, overdue."""
    item = db.query(ActionItem).filter(ActionItem.id == item_id).first()
    if not item:
        raise ValueError(f"Action item {item_id} not found.")
    item.status = status
    
    audit = AuditLog(
        user_id=user_id,
        action="UPDATE_ACTION_ITEM",
        details={"item_id": item_id, "new_status": status}
    )
    db.add(audit)
    db.commit()
    db.refresh(item)
    return item
