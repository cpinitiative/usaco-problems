git config --global user.name github-actions[bot]
git config --global user.email github-actions[bot]@users.noreply.github.com
git add .
git commit -m "auto-updates"
gh pr create -B main -H auto --title 'Problem auto-updates' --body 'Created by GitHub Actions'