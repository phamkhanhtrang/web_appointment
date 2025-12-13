# db_router.py
class DatabaseRouter:

    COMMON_MODELS = {
        'user',
        'doctor',
        'patient',
        'prescription',
        'prescriptiondetail',
        'doctorschedule',
        'specialty',
    }

    def db_for_read(self, model, **hints):
        if model._meta.model_name in self.COMMON_MODELS:
            return 'default'
        return None  # Django tự quyết

    def db_for_write(self, model, **hints):
        if model._meta.model_name in self.COMMON_MODELS:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self.COMMON_MODELS:
            return db == 'default'
        if model_name == 'appointment':
            return db in ['specialty1', 'specialty2']
        return False
