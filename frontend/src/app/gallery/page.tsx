"use client";

import { useEffect, useState } from "react";
import { listImages, getImageUrl, type ImageItem } from "@/lib/api";
import { ImageGrid } from "@/components/ImageGrid";

export default function GalleryPage() {
  const [images, setImages] = useState<ImageItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchImages() {
      try {
        const data = await listImages();
        setImages(data);
      } catch (error) {
        console.error("Failed to load images:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchImages();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto" />
        <p className="mt-4 text-gray-500">Loading images...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Image Gallery</h1>
        <p className="text-gray-600">
          Browse all {images.length} indexed images
        </p>
      </div>

      <ImageGrid
        images={images.map((img) => ({
          src: getImageUrl(img.payload.filename),
          filename: img.payload.filename,
        }))}
      />
    </div>
  );
}
