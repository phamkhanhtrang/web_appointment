class DatabaseRouter:
    COMMON_MODELS = {
        'user',
        'doctor',
        'patient',
        'doctorschedule',
        'specialty',
    }

    def db_for_read(self, model, **hints):
        if model._meta.model_name in self.COMMON_MODELS:
            return 'default'
        return None  # Appointment BẮT BUỘC dùng .using()

    def db_for_write(self, model, **hints):
        if model._meta.model_name in self.COMMON_MODELS:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db and obj2._state.db:
            return obj1._state.db == obj2._state.db
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self.COMMON_MODELS:
            return db == 'default'
        if model_name == 'appointment':
            return db in ['specialty1', 'specialty2']
        return False
