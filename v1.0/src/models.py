from sqlalchemy import Column, Integer, String, Date
from .database import Base

class DutySchedule(Base):
    """
    值班安排表的ORM模型
    映射到数据库中的 'duty_schedules' 表。
    现在支持多角色值班。
    """
    __tablename__ = "duty_schedules"

    id = Column(Integer, primary_key=True, index=True, doc="唯一标识，主键")
    duty_date = Column(Date, unique=True, nullable=False, index=True, doc="值班日期，唯一且非空")
    
    employee_full_professional = Column(String(255), nullable=True, doc="全专业值班")
    employee_cs_complaint = Column(String(255), nullable=True, doc="CS专业投诉值班")
    employee_cs_fault = Column(String(255), nullable=True, doc="CS专业故障值班")
    employee_ps_professional = Column(String(255), nullable=True, doc="PS专业值班")

    def __repr__(self):
        return (f"<DutySchedule(date='{self.duty_date}', "
                f"full='{self.employee_full_professional}', "
                f"cs_complaint='{self.employee_cs_complaint}')>")
