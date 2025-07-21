import unittest
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

# 将src目录添加到Python路径，以便导入我们的模块
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import models, services
from src.database import Base

class TestServices(unittest.TestCase):

    def setUp(self):
        """在每个测试用例运行前执行"""
        # 1. 设置一个内存中的SQLite数据库用于测试
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # 2. 创建一个临时的测试用Excel文件
        self.test_excel_path = "test_schedule.xlsx"
        self.create_test_excel()

    def tearDown(self):
        """在每个测试用例运行后执行"""
        self.db.close()
        # 清理临时的Excel文件
        if os.path.exists(self.test_excel_path):
            os.remove(self.test_excel_path)
    
    def create_test_excel(self):
        """辅助函数，创建一个用于测试的Excel文件"""
        date_col = '日期            平常：9:00-17:30\n周末：9:00-17:30'
        data = {
            date_col: [date(2024, 10, 1), date(2024, 10, 2)],
            '全专业值班': ['张三', '李四'],
            'CS专业投诉值班': ['王五', '赵六'],
            'CS专业故障值班': ['孙七', '周八'],
            'PS专业值班': ['吴九', '郑十']
        }
        df = pd.DataFrame(data)
        df.to_excel(self.test_excel_path, index=False)

    def test_import_schedule_from_excel(self):
        """测试从Excel成功导入数据的功能"""
        result = services.import_schedule_from_excel(self.db, self.test_excel_path)
        self.assertIn("成功导入了 2 条新值班记录", result)

        # 验证数据库中的数据
        schedules = self.db.query(models.DutySchedule).all()
        self.assertEqual(len(schedules), 2)

        schedule1 = schedules[0]
        self.assertEqual(schedule1.duty_date, date(2024, 10, 1))
        self.assertEqual(schedule1.employee_full_professional, '张三')
        self.assertEqual(schedule1.employee_cs_complaint, '王五')
        self.assertEqual(schedule1.employee_cs_fault, '孙七')
        self.assertEqual(schedule1.employee_ps_professional, '吴九')

    def test_get_duty_employee(self):
        """测试查询值班人员的功能"""
        # 先在数据库中手动创建一条记录
        test_record = models.DutySchedule(
            duty_date=date(2024, 11, 11),
            employee_full_professional="测试员A",
            employee_cs_complaint="测试员B",
            employee_ps_professional="测试员C" 
            # CS故障留空，测试None的情况
        )
        self.db.add(test_record)
        self.db.commit()

        # 测试查询存在的日期
        result = services.get_duty_employee(self.db, "2024-11-11")
        self.assertIn("2024年11月11日 的值班安排如下:", result)
        self.assertIn("全专业值班: 测试员A", result)
        self.assertIn("CS专业投诉值班: 测试员B", result)
        self.assertIn("CS专业故障值班: 无安排", result) # 验证None被正确处理
        self.assertIn("PS专业值班: 测试员C", result)

        # 测试查询不存在的日期
        result_not_found = services.get_duty_employee(self.db, "2025-01-01")
        self.assertIn("未找到 2025年01月01日 的值班记录", result_not_found)

    def test_swap_duty_schedule(self):
        """测试精准换班功能"""
        # 同样，先导入初始数据
        services.import_schedule_from_excel(self.db, self.test_excel_path)
        
        # 场景1: 同专业对调 (全专业值班: 张三 <-> 李四)
        services.swap_duty_schedule(self.db, "2024-10-01", "全专业值班", "2024-10-02", "全专业值班")
        
        schedule1_after_swap1 = self.db.query(models.DutySchedule).filter_by(duty_date=date(2024, 10, 1)).one()
        schedule2_after_swap1 = self.db.query(models.DutySchedule).filter_by(duty_date=date(2024, 10, 2)).one()
        
        self.assertEqual(schedule1_after_swap1.employee_full_professional, '李四')
        self.assertEqual(schedule2_after_swap1.employee_full_professional, '张三')

        # 场景2: 跨专业对调 (1号的CS投诉'王五' <-> 2号的PS专业'郑十')
        services.swap_duty_schedule(self.db, "2024-10-01", "CS专业投诉值班", "2024-10-02", "PS专业值班")

        schedule1_after_swap2 = self.db.query(models.DutySchedule).filter_by(duty_date=date(2024, 10, 1)).one()
        schedule2_after_swap2 = self.db.query(models.DutySchedule).filter_by(duty_date=date(2024, 10, 2)).one()

        self.assertEqual(schedule1_after_swap2.employee_cs_complaint, '郑十')
        self.assertEqual(schedule2_after_swap2.employee_ps_professional, '王五')

        # 场景3: 无效的角色名
        result = services.swap_duty_schedule(self.db, "2024-10-01", "不存在的专业", "2024-10-02", "全专业值班")
        self.assertIn("错误：无效的专业名称", result)

    # --- 测试用例将在这里添加 ---

if __name__ == '__main__':
    unittest.main() 