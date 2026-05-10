from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from apps.groups.models import Group, GroupMember
from apps.posts.models import Post


class Command(BaseCommand):
    help = "Seed demo data for local development."

    def _avatar_path(self, kind: str, slug: str) -> Path:
        root = Path(settings.MEDIA_ROOT) / "seed"
        root.mkdir(parents=True, exist_ok=True)
        return root / f"{kind}_{slug}.png"

    def _make_avatar(self, path: Path, label: str, bg: str) -> None:
        img = Image.new("RGB", (512, 512), bg)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 180)
        except OSError:
            font = ImageFont.load_default()
        text = label[:2].upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (512 - (bbox[2] - bbox[0])) / 2 - bbox[0]
        y = (512 - (bbox[3] - bbox[1])) / 2 - bbox[1]
        draw.ellipse((24, 24, 488, 488), outline=(255, 255, 255), width=8)
        draw.text((x, y), text, fill="white", font=font)
        img.save(path)

    def _pick_color(self, index: int) -> str:
        colors = [
            "#ff7a2f",
            "#35d07f",
            "#ff5fa2",
            "#ff3b5c",
            "#4f86ff",
            "#9b5cff",
            "#ffb02e",
            "#2ecc71",
        ]
        return colors[index % len(colors)]

    def handle(self, *args, **options):
        User = get_user_model()

        users_seed = [
            ("amanraj", "Aman Raj", "amanraj@example.com", "male", 24),
            ("adityagu", "Aditya Gupta", "adityagu@example.com", "male", 23),
            ("rahulsh", "Rahul Sharma", "rahulsh@example.com", "male", 25),
            ("rohanme", "Rohan Mehta", "rohanme@example.com", "male", 22),
            ("priyaka", "Priya Kapoor", "priyaka@example.com", "female", 21),
            ("nehaaa", "Neha Singh", "nehaaa@example.com", "female", 23),
            ("varundh", "Varun Dhawan", "varundh@example.com", "male", 26),
            ("anjalij", "Anjali Jain", "anjalij@example.com", "female", 24),
            ("ishasen", "Isha Sen", "ishasen@example.com", "female", 22),
            ("kabirkm", "Kabir Kumar", "kabirkm@example.com", "male", 25),
            ("tanvim", "Tanvi Malhotra", "tanvim@example.com", "female", 23),
            ("arjundh", "Arjun Desai", "arjundh@example.com", "male", 24),
            ("meerana", "Meera Nair", "meerana@example.com", "female", 22),
            ("kunalb", "Kunal Bose", "kunalb@example.com", "male", 27),
            ("sanyash", "Sanya Sethi", "sanyash@example.com", "female", 21),
            ("pratikp", "Pratik Patel", "pratikp@example.com", "male", 25),
            ("ritika", "Ritika Verma", "ritika@example.com", "female", 24),
            ("yashj", "Yash Joshi", "yashj@example.com", "male", 23),
            ("nikhilr", "Nikhil Rao", "nikhilr@example.com", "male", 26),
            ("sanjan", "Sanjana Pillai", "sanjan@example.com", "female", 22),
            ("aakashk", "Aakash Khanna", "aakashk@example.com", "male", 24),
            ("shreyam", "Shreya Mishra", "shreyam@example.com", "female", 23),
            ("vivekb", "Vivek Bansal", "vivekb@example.com", "male", 28),
            ("divyas", "Divya Shah", "divyas@example.com", "female", 21),
            ("harshaa", "Harsha Agarwal", "harshaa@example.com", "male", 24),
            ("poojaa", "Pooja Anand", "poojaa@example.com", "female", 22),
            ("tarunk", "Tarun Kumar", "tarunk@example.com", "male", 26),
            ("rheaaa", "Rhea Arora", "rheaaa@example.com", "female", 20),
            ("sidhar", "Siddharth Rao", "sidhar@example.com", "male", 27),
            ("madhavp", "Madhav Patil", "madhavp@example.com", "male", 23),
        ]

        users = []
        for index, (unique_name, full_name, email, gender, age) in enumerate(users_seed):
            user, created = User.objects.get_or_create(
                unique_name=unique_name,
                defaults={"email": email, "full_name": full_name},
            )
            user.email = email
            user.full_name = full_name
            user.set_password("aditya@123")
            user.save()

            profile = user.profile
            profile.display_name = full_name
            profile.gender = gender
            profile.age = age
            profile.bio = "Building a clean social platform."
            avatar_path = self._avatar_path("user", unique_name)
            self._make_avatar(avatar_path, unique_name, self._pick_color(index))
            profile.avatar.name = str(avatar_path.relative_to(settings.MEDIA_ROOT)).replace("\\", "/")
            profile.save()
            users.append(user)

        group_seed = [
            (
                "Coding Hub",
                "A space for Python, webdev, AI, and startup builders.",
                "coding,python,webdev,ai,startup,design,editing",
            ),
            (
                "Cricket Corner",
                "Discuss matches, players, fantasy picks, and live scores.",
                "cricket,fitness,gym,food,memes,football,stocks",
            ),
            (
                "Bollywood Beats",
                "Movies, music, fashion, and entertainment talk.",
                "movies,music,fashion,poetry,memes,editing,photography",
            ),
            (
                "Study Squad",
                "Books, productivity, notes, and serious learning.",
                "books,poetry,design,webdev,python,ai,startup",
            ),
            (
                "Street Food Club",
                "Food, travel, cafés, and local discoveries.",
                "food,travel,photography,fashion,memes,books,fitness",
            ),
        ]

        groups = []
        for index, (name, description, tags) in enumerate(group_seed):
            group, created = Group.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "admin": users[index % len(users)],
                    "tags": tags,
                    "public_join": True,
                    "rules": "Be respectful and keep it clean.",
                },
            )
            group.description = description
            group.admin = users[index % len(users)]
            group.tags = tags
            group.public_join = True
            group.rules = "Be respectful and keep it clean."
            group_dp = self._avatar_path("group", name.lower().replace(" ", "_"))
            self._make_avatar(group_dp, name, self._pick_color(index + 3))
            group.display_picture.name = str(group_dp.relative_to(settings.MEDIA_ROOT)).replace("\\", "/")
            group.save()
            groups.append(group)

        for user in users:
            for group in groups:
                GroupMember.objects.get_or_create(group=group, user=user)

        Post.objects.get_or_create(author=users[0], content="Welcome to VIBE-Z!")
        Post.objects.get_or_create(author=users[1], content="Ready for some group chats and calls.")
        self.stdout.write(self.style.SUCCESS("Demo users and groups created."))
