def get_list_display(self, request):
        my_list_display = super().get_list_display(request)
        if request.user.username == "noparents":
            my_list_display = list(my_list_display)
            my_list_display.remove("parent")
        return my_list_display