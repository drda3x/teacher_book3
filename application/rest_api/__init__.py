#!/usr/bin/env python
# -*- coding: utf-8 -*-


from groups import (
    get_list,
    get_base_info,
    process_lesson,
    delete_lessons,
    move_lessons,
    cancel_lesson,
    restore_lesson,
    delete_student,
    change_group
)
from students import edit_student
from auth import login, logout
from comments import edit_comment
from system import view_changes
