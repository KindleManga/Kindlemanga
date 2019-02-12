# Kindlemanga
Generate *Kindle* friendly manga. Good for your eyes and your feelings.  

# Requirements  
Download [Kindlegen](https://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211),  
then extract it with `tar xzf`, then `sudo cp kindlegen /usr/local/bin` and you are good to go.  

Fill your secret data to `.env` file, with format from `.env.example`  

Then run `celery -A main worker -l debug` in `manga_web`

# Kindlemanga 1.0 - Bring manga to you Kindle.  

#### Step 1:  
Search your favorite manga

#### Step 2:
Enter your Kindle Email(Coming soon) or your Email.  

#### Step 3:
We will send the manga directly to your Kindle, or notify to your Email when your Manga ready to download.  

#### Step 4:
Let's read!!

![gintama](https://media.giphy.com/media/BWAS8JjjZgh6o/giphy.gif)


# Development  
This project is base on KCC and Django. Please contribute as much as you want!
