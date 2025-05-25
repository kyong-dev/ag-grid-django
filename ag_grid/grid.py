class AgGrid:
    list_display = None
    editable = []
    sortable = []
    form_fields = {}

    @classmethod
    def get_list_display(cls):
        return cls.list_display

    @classmethod
    def get_editable_fields(cls):
        return cls.editable

    @classmethod
    def get_sortable_fields(cls):
        return cls.sortable

    @classmethod
    def get_form_fields(cls):
        return cls.form_fields
