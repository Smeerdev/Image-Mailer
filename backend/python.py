from googleapiclient.discovery import build
import requests
from PIL import Image
from io import BytesIO
import os
import zipfile
import json
import sys
import warnings
import time
warnings.filterwarnings("ignore", category=UserWarning, module="PIL.Image")

API_KEY = "API_KEY"
CX = "SEARCH_ENGINE_ID"

def download_images(query, num_images):
    service = build("customsearch", "v1", developerKey=API_KEY)

    output_dir = "downloaded_images"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    images_downloaded = 0
    start_index = 1
    failed_urls = []
    seen_urls = set()  

    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        )
    }

    while images_downloaded < num_images:
        num_to_fetch = min(10, num_images - images_downloaded)

        try:
            res = service.cse().list(
                q=query,
                cx=CX,
                searchType="image",
                start=start_index,
                num=num_to_fetch
            ).execute()
        except Exception as e:
            print(f"Google API error: {e}", file=sys.stderr)
            break

        if "items" not in res:
            break

        for item in res["items"]:
            if images_downloaded >= num_images:
                break

            img_url = item.get("link")
            if not img_url or img_url in seen_urls: 
                continue
            seen_urls.add(img_url)

            success = False
            for attempt in range(3):  
                try:
                    response = session.get(img_url, headers=headers, timeout=15)
                    response.raise_for_status()

                    if images_downloaded < num_images:
                        img = Image.open(BytesIO(response.content)).convert("RGB")
                        filename = os.path.join(output_dir, f"{query}_{images_downloaded+1}.jpg")
                        img.save(filename)
                        images_downloaded += 1
                    else:
                        break
                    success = True
                    print(f"Downloaded: {filename}", file=sys.stderr)
                    break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed for {img_url}: {e}", file=sys.stderr)
                    time.sleep(2)

            if not success:
                failed_urls.append(img_url)
                print(f"Skipped after retries: {img_url}", file=sys.stderr)

        start_index += 10

    if images_downloaded == 0:
        raise Exception("No images could be downloaded.")
    if failed_urls:
        with open("failed_urls.txt", "w") as f:
            for u in failed_urls:
                f.write(u + "\n")

    zip_filename = f"{query}_images.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for img_file in os.listdir(output_dir):
            zipf.write(os.path.join(output_dir, img_file), img_file)

    for file in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, file))
    os.rmdir(output_dir)

    result = {
        "zip_path": zip_filename,  
        "message": f"Downloaded {images_downloaded} images successfully. "
    }
    return result

def main():
    try:
        keyword = sys.argv[1]
        num_images = int(sys.argv[2])
        result = download_images(keyword, num_images)
        print(json.dumps(result))
    except Exception as e:
        error_result = {"error": str(e)}
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()