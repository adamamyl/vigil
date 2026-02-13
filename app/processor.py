import os
import yt_dlp
from loguru import logger
from datetime import datetime
from app.database import Session, DownloadQueue

def run_sweep():
    with Session() as session:
        # Only grab items that actually need work
        queue = session.query(DownloadQueue).filter(
            DownloadQueue.status.in_(["pending", "failed"])
        ).all()
        
        if not queue:
            logger.info("😴 Sweep finished: Nothing new to download.")
            return
        
        download_base = os.getenv("DOWNLOAD_DIR", "/downloads")
        
        for item in queue:
            item.status = "downloading"
            session.commit()
            
            try:
                date_str = datetime.now().strftime("%Y-%m")
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                    'merge_output_format': 'mp4',
                    'download_archive': os.path.join(download_base, ".archive.txt"),
                    'outtmpl': f"{download_base}/{date_str}/%(extractor)s/%(title)s.%(ext)s",
                    'quiet': True,
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([item.url])
                
                item.status = "completed"
                logger.info(f"Successfully processed: {item.url}")
            except Exception as e:
                logger.error(f"Error processing {item.url}: {e}")
                item.status = "failed"
            
            session.commit()