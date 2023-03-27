import re
import requests
import time

import argparse

parser = argparse.ArgumentParser(description="FAI generator")
parser.add_argument("--username", required=True, help="username")
parser.add_argument("--userpw", required=True, help="password")
parser.add_argument("--suite", required=True, help="Debian suite (buster/bullseye/bookworm)")
parser.add_argument("--desktop", help="desktop environment")
parser.add_argument("--target", required=True, help="target destination of created image")

args = parser.parse_args()

url_template = "https://fai-project.org/cgi/faime.cgi?type=install;username={username};userpw={userpw};partition=ONE;keyboard=us;suite={suite};l5=SSH_SERVER;cl6=STANDARD;cl7=NONFREE;rclocal=1;sbm=2{desktop}"

desktop_arg = ";desktop=" + args.desktop if args.desktop else ""

url = url_template.format(
    username=args.username,
    userpw=args.userpw,
    suite=args.suite,
    desktop=desktop_arg,
)

print("Generated URL:", url)

response = requests.get(url) # prepare job to generate

if response.status_code == 200:
    pattern = r'statuspage:\s*(\S+)'  # regular expression to match the URL after "statuspage:"
    match = re.search(pattern, response.text)  # search for the pattern in the response text
    if match:
        job_url = match.group(1)  # extract the URL after "statuspage:"
        
        print("Job URL:", job_url)
        print("Generating image.....")
        
        pattern_waiting = r'Your job (\w{8}) is waiting for processing\.' 
        pattern_processing = r'Your job (\w{8}) is currently being processed\.'
        
        while True:
            response = requests.get(job_url)
            if response.status_code != 200:
                print("Failed to curl website. Status code:", response.status_code)
                break  # exit the loop if the request fails
            
            match_waiting = re.search(pattern_waiting, response.text)  # search for the pattern in the response text
            match_processing = re.search(pattern_processing, response.text)

            if not (match_waiting or match_processing):
                print("Image generation successful")
                break  # exit the loop if the job processing is completed

            time.sleep(5) # sleep instead of curling all the time

        pattern = r'Your customized FAI.me image is ready for downloaded from <br> <a href="([^"]+)">'  # regular expression pattern to match the URL inside the ahref attribute
        match = re.search(pattern, response.text)  # search for the pattern in the response text

        if match:
            download_url = match.group(1)  # extract the URL from the matched string

            print("Download URL:", download_url)
            print("Downloading image....")

            response_img = requests.get(download_url)

            with open(args.target, "wb") as f:
                f.write(response_img.content)

            print("Succesfully downloaded image")

        else:
            print("Failed to generate image.")

    else:
        print("Failed to find URL for the created job. The website may have changed its format.")
else:
    print("Failed to initiate debian image generation. Try again")