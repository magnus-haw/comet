from django.urls import path
from . import views

urlpatterns = [
    path("rooms/current/", views.current_rooms_view, name="current-rooms"),
    path("rooms/projection/<int:year>/<int:month>/", views.future_projection_view, name="future-projection"),
]

urlpatterns += [
    path('enrollment/', views.enrollment, name='enrollment'),
]

urlpatterns += [
    path('withdrawals/add/', views.add_withdrawal, name='add_withdrawal'),
    path('withdrawals/add/<int:child_pk>/', views.add_withdrawal, name='add_withdrawal_for_child'),
    path('withdrawals/edit/<int:w_pk>/', views.add_withdrawal, name='edit_withdrawal'),
    path('withdrawals/delete/<int:w_pk>/', views.delete_withdrawal, name='delete_withdrawal'),
    path('withdrawals/<int:w_pk>/send-email/', views.send_withdrawal_email, name='send_withdrawal_email'),
    path('withdrawals/<int:w_pk>/implement/', views.implement_withdrawal, name='implement_withdrawal'),
]

urlpatterns += [
    path('transitions/add/', views.add_transition, name='add_transition'),
    path('transitions/add/<int:child_pk>/', views.add_transition, name='add_transition_for_child'),
    path('transitions/edit/<int:trans_pk>/', views.add_transition, name='edit_transition'),
    path('transitions/delete/<int:trans_pk>/', views.delete_transition, name='delete_transition'),
    path('transitions/<int:transition_id>/', views.transition_detail, name='transition_detail'),
    path('transitions/<int:transition_id>/send-email/', views.send_transition_email, name='send_transition_email'),
    path('transitions/<int:transition_id>/implement/', views.implement_transition, name='implement_transition'),
]
