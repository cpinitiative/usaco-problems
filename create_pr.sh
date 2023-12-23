git config --global user.name github-actions[bot]
git config --global user.email github-actions[bot]@users.noreply.github.com
git add .
git commit -m "auto-updates"
git push -f origin auto
gh pr create --title 'Problem auto-updates' -F out/report.txt