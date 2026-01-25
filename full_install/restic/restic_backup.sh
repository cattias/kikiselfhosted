#!/bin/bash

# --- Backup ---
restic backup /volume1/backup --repo "sftp:restic_user@offsite.kiki.home:restic_repository" --password-file /home/kiki/restic/restic_password.txt --exclude-caches --tag "offsite_daily" --verbose

# --- Cleanup Command (Maintenance) ---
# Keeps 7 daily, 4 weekly, 12 monthly, and 1 yearly snapshot.
restic forget --repo "sftp:restic_user@offsite.kiki.home:restic_repository" --password-file /home/kiki/restic/restic_password.txt --prune --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --keep-yearly 1

exit $?
