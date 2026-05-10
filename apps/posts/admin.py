from django.contrib import admin
from .models import Post, PostReaction, Comment, PostSave


admin.site.register(Post)
admin.site.register(PostReaction)
admin.site.register(Comment)
admin.site.register(PostSave)
