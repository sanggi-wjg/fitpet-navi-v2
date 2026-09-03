from sqlalchemy.orm import Session

from fitpet_navi.domain.task.task_section import TaskSection


class TaskSectionRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_all(self, task_sections: list[TaskSection]) -> list[TaskSection]:
        self.session.add_all(task_sections)
        self.session.flush()
        return task_sections
