from sqlalchemy import Column, Integer, String, Date, DateTime, func
from .database import Base
import datetime

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


class SwapLog(Base):
    """用于记录换班操作的审计日志表。"""
    __tablename__ = "swap_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_time = Column(DateTime(timezone=True), server_default=func.now(), comment="日志记录时间")
    
    date1 = Column(Date, nullable=False, comment="第一个对调日期")
    role1 = Column(String(255), nullable=False, comment="第一个对调的专业")
    original_employee1 = Column(String(255), nullable=True, comment="第一个日期的原值班员")
    new_employee1 = Column(String(255), nullable=True, comment="第一个日期的新值班员 (即原date2的值班员)")

    date2 = Column(Date, nullable=False, comment="第二个对调日期")
    role2 = Column(String(255), nullable=False, comment="第二个对调的专业")
    original_employee2 = Column(String(255), nullable=True, comment="第二个日期的原值班员")
    new_employee2 = Column(String(255), nullable=True, comment="第二个日期的新值班员 (即原date1的值班员)")
