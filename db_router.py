# db_router.py
class DatabaseRouter:
    """
    Router cho nhiều database:
    - DB_Chung: User, Doctor, Patient, Prescription, PrescriptionDetail
    - DB_KhoaX: Appointment, DoctorSchedule theo specialty_id
    """
    def db_for_read(self, model, **hints):
        if model._meta.model_name in ['doctor', 'patient', 'prescription', 'prescriptiondetail']:
            return 'default'
        elif model._meta.model_name in ['appointment', 'doctorschedule']:
            specialty_id = hints.get('specialty_id')
            if specialty_id == 1:
                return 'specialty1'
            elif specialty_id == 2:
                return 'specialty2'
        return 'default'

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        # Cho phép relation nếu 2 object ở cùng DB
        db_list = ['default', 'specialty1', 'specialty2']
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Chỉ migrate model vào database tương ứng
        if model_name in ['doctor', 'patient', 'prescription', 'prescriptiondetail']:
            return db == 'default'
        elif model_name in ['doctorschedule', 'appointment']:
            return db in ['specialty1', 'specialty2']
        return None