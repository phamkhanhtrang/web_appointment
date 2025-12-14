class DatabaseRouter:
    COMMON_MODELS = {
        'user',
        'doctor',
        'patient',
        'doctorschedule',
        'specialty',
    }

    APPOINTMENT_MODELS = {
        'appointment',
        'prescription',
        'prescriptiondetail',
    }

    def db_for_read(self, model, **hints):
        model_name = model._meta.model_name
        if model_name in self.COMMON_MODELS:
            return 'default'
        if model_name in self.APPOINTMENT_MODELS:
            # Nếu hint chứa 'specialty_id', chọn DB tương ứng
            specialty_id = hints.get('specialty_id')
            if specialty_id == 1:
                return 'specialty1'
            elif specialty_id == 2:
                return 'specialty2'
            # default fallback
            return 'specialty1'
        return None

    def db_for_write(self, model, **hints):
        model_name = model._meta.model_name
        if model_name in self.COMMON_MODELS:
            return 'default'
        if model_name in self.APPOINTMENT_MODELS:
            specialty_id = hints.get('specialty_id')
            if specialty_id == 1:
                return 'specialty1'
            elif specialty_id == 2:
                return 'specialty2'
            return 'specialty1'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        # Chỉ cho phép relation trong cùng DB
        if obj1._state.db and obj2._state.db:
            return obj1._state.db == obj2._state.db
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self.COMMON_MODELS:
            return db == 'default'
        if model_name == 'appointment' or model_name in ['prescription', 'prescriptiondetail']:
            return db in ['specialty1', 'specialty2']
        return False
