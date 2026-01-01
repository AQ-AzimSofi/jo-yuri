"use client";

import { useState, useRef } from "react";
import { indexModelStream } from "@/lib/api";

interface IndexingProgressProps {
  modelId: string;
  modelName: string;
  onComplete?: () => void;
  onClose: () => void;
}

export function IndexingProgress({
  modelId,
  modelName,
  onComplete,
  onClose,
}: IndexingProgressProps) {
  const [status, setStatus] = useState<"idle" | "indexing" | "complete" | "error">("idle");
  const [progress, setProgress] = useState({ current: 0, total: 0, file: "" });
  const [errors, setErrors] = useState<string[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startIndexing = () => {
    setStatus("indexing");
    setErrors([]);

    eventSourceRef.current = indexModelStream(modelId, (data) => {
      if (data.status === "loading_model") {
        setProgress({ current: 0, total: data.total || 0, file: "Loading model..." });
      } else if (data.status === "starting") {
        setProgress({ current: 0, total: data.total || 0, file: "" });
      } else if (data.status === "indexing") {
        setProgress({
          current: data.current || 0,
          total: data.total || 0,
          file: data.file || "",
        });
      } else if (data.status === "file_error") {
        setErrors((prev) => [...prev, `${data.file}: ${data.error}`]);
        setProgress((prev) => ({
          ...prev,
          current: data.current || prev.current,
          total: data.total || prev.total,
        }));
      } else if (data.status === "complete") {
        setStatus("complete");
        eventSourceRef.current?.close();
        onComplete?.();
      } else if (data.status === "error") {
        setStatus("error");
        setErrors((prev) => [...prev, data.error || "Unknown error"]);
        eventSourceRef.current?.close();
      }
    });
  };

  const handleClose = () => {
    eventSourceRef.current?.close();
    onClose();
  };

  const percentage = progress.total > 0 ? (progress.current / progress.total) * 100 : 0;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-semibold mb-4">Index Images with {modelName}</h3>

        {status === "idle" && (
          <>
            <p className="text-gray-600 mb-4">
              This will generate embeddings for all images using the selected model.
              Depending on the number of images, this may take several minutes.
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={handleClose}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={startIndexing}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Start Indexing
              </button>
            </div>
          </>
        )}

        {status === "indexing" && (
          <>
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Progress</span>
                <span>
                  {progress.current} / {progress.total}
                </span>
              </div>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-purple-600 transition-all duration-300 ease-out"
                  style={{ width: `${percentage}%` }}
                />
              </div>
              {progress.file && (
                <p className="text-xs text-gray-500 mt-2 truncate">
                  Processing: {progress.file}
                </p>
              )}
            </div>
            {errors.length > 0 && (
              <div className="text-sm text-yellow-600 mb-2 max-h-20 overflow-y-auto">
                {errors.length} file(s) had errors
              </div>
            )}
          </>
        )}

        {status === "complete" && (
          <>
            <div className="text-center mb-4">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg
                  className="w-6 h-6 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <p className="text-green-600 font-medium">
                Successfully indexed {progress.total} images
              </p>
              {errors.length > 0 && (
                <p className="text-sm text-yellow-600 mt-1">
                  ({errors.length} files had errors)
                </p>
              )}
            </div>
            <div className="flex justify-end">
              <button
                onClick={handleClose}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Done
              </button>
            </div>
          </>
        )}

        {status === "error" && (
          <>
            <div className="text-center mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg
                  className="w-6 h-6 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <p className="text-red-600 font-medium">Indexing failed</p>
              {errors.length > 0 && (
                <p className="text-sm text-gray-600 mt-1">{errors[errors.length - 1]}</p>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={handleClose}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setStatus("idle");
                  setErrors([]);
                }}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
