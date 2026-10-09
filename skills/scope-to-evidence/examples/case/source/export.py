"""Synthetic fixture for skill evaluation; not a production export implementation."""
import csv
import io


def export_csv(users):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["name", "email"])
    writer.writerows((user["name"], user["email"]) for user in users)
    return stream.getvalue().encode("utf-8")


def directory_users():
    return [{"name": "Demo", "email": "demo@example.invalid"}]


def export_directory():
    return export_csv(directory_users())
