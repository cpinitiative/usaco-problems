import modal
import usaco_scraper
import generate_probgate_mapping
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
    usaco_scraper.main()
    probgate_contests_scraper.main()
    generate_probgate_mapping.main()
