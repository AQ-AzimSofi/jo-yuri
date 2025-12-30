"use client";

import { useState } from "react";

interface ImageItem {
  src: string;
  filename: string;
  score?: number;
}

interface ImageGridProps {
  images: ImageItem[];
}

export function ImageGrid({ images }: ImageGridProps) {
  const [selectedImage, setSelectedImage] = useState<ImageItem | null>(null);

  if (images.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">No images found</div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {images.map((image) => (
          <div
            key={image.filename}
            className="relative group cursor-pointer rounded-lg overflow-hidden bg-gray-100 aspect-square"
            onClick={() => setSelectedImage(image)}
          >
            <img
              src={image.src}
              alt={image.filename}
              className="w-full h-full object-cover transition-transform group-hover:scale-105"
            />
            {image.score !== undefined && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                <span className="text-white text-sm">
                  Score: {(image.score * 100).toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh]">
            <img
              src={selectedImage.src}
              alt={selectedImage.filename}
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
            />
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-2 right-2 w-8 h-8 bg-white/20 hover:bg-white/40 rounded-full flex items-center justify-center text-white transition-colors"
            >
              X
            </button>
            <div className="absolute bottom-2 left-2 bg-black/50 px-2 py-1 rounded text-white text-sm">
              {selectedImage.filename}
              {selectedImage.score !== undefined && (
                <span className="ml-2">
                  ({(selectedImage.score * 100).toFixed(1)}%)
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
