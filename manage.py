# #!/usr/bin/env python
# import os
# import sys

# def main():
#     """Run administrative tasks."""
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phish_titan.settings')
#     try:
#         from django.core.management import execute_from_command_line
#     except ImportError as exc:
#         raise ImportError(
#             "Couldn't import Django. Make sure it's installed and your virtual environment is active."
#         ) from exc
#     execute_from_command_line(sys.argv)

# if __name__ == '__main__':
#     main()
#!/usr/bin/env python
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phish_titan.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it's installed and your virtual environment is active."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()