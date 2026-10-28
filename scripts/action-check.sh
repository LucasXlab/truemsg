#!/usr/bin/env bash
set -euo pipefail
if ! cd -- "${TRUEMSG_WORKDIR:-.}"; then
  echo "Unable to access the selected working tree" >&2
  exit 2
fi
case "${TRUEMSG_FAIL_ON:-fail}" in fail|warn) ;; *) echo 'Invalid fail-on threshold' >&2; exit 2;; esac
if [[ -n "${TRUEMSG_RANGE:-}" ]]; then
  truemsg check --range "$TRUEMSG_RANGE" --fail-on "${TRUEMSG_FAIL_ON:-fail}"
elif [[ -n "${TRUEMSG_PR_TITLE:-}" ]]; then
  truemsg check --pr --base "$TRUEMSG_BASE" --head "$TRUEMSG_HEAD" --title "$TRUEMSG_PR_TITLE" --body "${TRUEMSG_PR_BODY:-}" --fail-on "${TRUEMSG_FAIL_ON:-fail}"
elif [[ -n "${TRUEMSG_BASE:-}" && ! "$TRUEMSG_BASE" =~ ^0+$ ]]; then
  truemsg check --range "$TRUEMSG_BASE..$TRUEMSG_HEAD" --fail-on "${TRUEMSG_FAIL_ON:-fail}"
else
  truemsg check --ref "${TRUEMSG_HEAD:-HEAD}" --fail-on "${TRUEMSG_FAIL_ON:-fail}"
fi
