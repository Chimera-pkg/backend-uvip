import httpx
import asyncio
import os
from uuid import UUID
from fastapi import BackgroundTasks
from app.db.database import SessionLocal
from app.db.models import StreetPhoto, SegmentationResult, PerceptionPrediction, VideoOutputSegmentation
from app.db.enums import ProcessingStatus

async def process_photo_with_ai_task(photo_id: UUID, file_path: str):
    """
    Fungsi worker yang berjalan di background untuk memanggil API AI
    dan menyimpan hasilnya ke database.
    """
    db = SessionLocal() # Buka session DB baru khusus untuk background task
    try:
        # 1. Update status foto menjadi processing
        photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
        if not photo:
            return
        
        photo.processing_status = ProcessingStatus.SEGMENTING
        db.commit()

        # 2. Panggil API AI
        ai_url = "http://80.241.214.39:8002/ai/process"
        
        async with httpx.AsyncClient(timeout=120.0) as client: # Timeout 2 menit untuk proses AI
            with open(file_path, "rb") as f:
                # Siapkan file dan payload
                files = {"file": (os.path.basename(file_path), f, "image/jpeg")}
                data = {"photo_id": str(photo_id)}
                
                # Eksekusi POST request
                response = await client.post(ai_url, data=data, files=files)
                
        response.raise_for_status()
        result = response.json()

        # 3. Insert Data Segmentation Result
        seg_data = result.get("segmentation_results", {})
        segmentation = SegmentationResult(
            photo_id=photo_id,
            model_name="AI-Pipeline-V1",
            green_coverage_pct=seg_data.get("green_coverage_pct", 0),
            building_coverage_pct=seg_data.get("building_coverage_pct", 0),
            walkability_ratio=seg_data.get("walkability_ratio", 0),
            visual_clutter_index=seg_data.get("visual_clutter_index", 0),
            sky_visibility_pct=seg_data.get("sky_visibility_pct", 0),
            segmentation_url=result.get("segmentation_url", ""),
            privacy_masked_url=result.get("privacy_masked_url", ""),
            segmentation_overlay_url=result.get("segmentation_overlay_url", "")
        )
        db.add(segmentation)
        db.flush() # Flush agar segmentation.id ter-generate untuk tabel child

        # 4. Insert Data Perception Prediction
        perc_data = result.get("perception_prediction", {})
        prediction = PerceptionPrediction(
            photo_id=photo_id,
            segmentation_id=segmentation.id, # Terhubung ke relasi segmentasi
            beauty_score=perc_data.get("beauty_score", 0),
            safety_score=perc_data.get("safety_score", 0),
            comfort_score=perc_data.get("comfort_score", 0),
            uvi_score=perc_data.get("uvi_score", 0)
        )
        db.add(prediction)

        # 5. Update Status Foto Selesai
        photo.privacy_masked = True if result.get("privacy_masked_url") else False
        photo.processing_status = ProcessingStatus.COMPLETED
        db.commit()

    except Exception as e:
        # Tangani error jika AI gagal atau API down
        db.rollback()
        photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
        if photo:
            photo.processing_status = ProcessingStatus.FAILED
            photo.error_message = f"AI Processing Error: {str(e)}"
            db.commit()
    finally:
        db.close() # Tutup koneksi DB agar tidak bocor

async def process_video_with_ai_task(video_id: UUID, file_path: str):
    """
    Worker background untuk mengunggah video ke server AI, melakukan polling 
    sampai selesai, dan menyimpan hasil akhirnya ke tabel video_outputs.
    """
    db = SessionLocal()
    try:
        # 1. Update status video menjadi sedang diproses
        video = db.query(StreetPhoto).filter(StreetPhoto.id == video_id).first()
        if not video:
            return
        
        video.processing_status = ProcessingStatus.SEGMENTING # atau status enum yang relevan
        db.commit()

        ai_post_url = "http://80.241.214.39:8002/ai/process-video"
        
        # 2. POST Video ke AI
        # Menggunakan timeout yang agak panjang untuk antisipasi upload file besar ke server AI
        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "video/mp4")}
                # Sesuaikan default fps & overlay_alpha jika diperlukan
                data = {
                    "photo_id": str(video_id),
                    "fps": "20.0", 
                    "overlay_alpha": "0.5"
                }
                
                post_response = await client.post(ai_post_url, data=data, files=files)
            
            post_response.raise_for_status()
            task_data = post_response.json()
            task_id = task_data.get("task_id")

            if not task_id:
                raise ValueError("Server AI tidak mengembalikan task_id")

            # 3. Polling API Result (Mengecek setiap 30 detik)
            ai_result_url = f"http://80.241.214.39:8002/ai/process-video/result/{task_id}"
            
            while True:
                result_response = await client.get(ai_result_url, timeout=30.0)
                
                if result_response.status_code == 202:
                    # Masih processing, tunggu 30 detik sebelum cek lagi
                    await asyncio.sleep(60)
                    continue
                elif result_response.status_code == 200:
                    # Proses selesai, keluar dari loop
                    final_data = result_response.json()
                    break
                else:
                    # Menangani error dari server AI
                    result_response.raise_for_status()

        # 4. Insert data hasil proses ke VideoOutputSegmentation
        video_info = final_data.get("video_info", {})
        
        video_output = VideoOutputSegmentation(
            photo_id=video_id,
            video_url=final_data.get("video_url", ""),
            fps=video_info.get("fps", 0.0),
            frame_count=video_info.get("frame_count", 0.0),
            width=video_info.get("width", 0.0),
            height=video_info.get("height", 0.0),
            duration_seconds=video_info.get("duration_seconds", 0.0),
            frames_processed=final_data.get("frames_processed", 0.0),
            processing_time_ms=final_data.get("processing_time_ms", 0.0)
        )
        db.add(video_output)

        # 5. Update Status StreetPhoto menjadi selesai
        video.processing_status = ProcessingStatus.COMPLETED
        db.commit()

    except Exception as e:
        db.rollback()
        video = db.query(StreetPhoto).filter(StreetPhoto.id == video_id).first()
        if video:
            video.processing_status = ProcessingStatus.FAILED
            video.error_message = f"AI Video Error: {str(e)}"
            db.commit()
    finally:
        db.close()