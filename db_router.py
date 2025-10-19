# db_router.py
class DatabaseRouter:
    """
    Định tuyến cơ sở dữ liệu:
    - Ghi (INSERT, UPDATE, DELETE) → master
    - Đọc (SELECT) → slave
    """
    def db_for_read(self, model, **hints):
        return 'slave'

    def db_for_write(self, model, **hints):
        return 'default'  # master

    def allow_relation(self, obj1, obj2, **hints):
        # Cho phép quan hệ giữa các model nếu cùng DB
        db_list = ('default', 'slave')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Chỉ migrate trên master
        return db == 'default'
