class AgGrid:
    list_display = None
    editable = []
    sortable = []
    left_pinning = []
    right_pinning = []
    header_names = {}
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
    def get_left_pinning(cls):
        return cls.left_pinning

    @classmethod
    def get_right_pinning(cls):
        return cls.right_pinning

    @classmethod
    def get_header_names(cls):
        return cls.header_names

    @classmethod
    def get_form_fields(cls):
        return cls.form_fields

    @classmethod
    def get_fk_display_field(cls, field_name):
        """
        if field_name == "your_foreign_key_field":
            return "name"
        """
        return None
