import modal
import probgate_contests_scraper

app = modal.App(
    "usaco-problems",
    image=modal.Image.debian_slim().pip_install("requests", "bs4", "python-dotenv"),
    volumes={
        "/root/data_private": modal.Volume.from_name(
            "usaco-problems", create_if_missing=True
        )
    },
)


@app.function(secrets=[modal.Secret.from_name("probgate")])
def scrape():
    probgate_contests_scraper.main()
