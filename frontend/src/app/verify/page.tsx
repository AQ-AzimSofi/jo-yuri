"use client";

import { useState, useCallback } from "react";
import { verifyImage, type VerifyResponse } from "@/lib/api";

export default function VerifyPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = (file: File) => {
    setFile(file);
    setResult(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.type.startsWith("image/")) {
      handleFile(droppedFile);
    }
  }, []);

  const handleVerify = async () => {
    if (!file) return;

    setLoading(true);
    try {
      const response = await verifyImage(file);
      setResult(response);
    } catch (error) {
      console.error("Verification failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Face Verification
        </h1>
        <p className="text-gray-600">
          Upload an image to check if it contains Jo Yuri
        </p>
      </div>

      <div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          dragActive
            ? "border-purple-500 bg-purple-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
      >
        {preview ? (
          <div className="space-y-4">
            <img
              src={preview}
              alt="Preview"
              className="max-h-64 mx-auto rounded-lg"
            />
            <p className="text-sm text-gray-500">{file?.name}</p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-600">
              Drag and drop an image here, or click to select
            </p>
          </div>
        )}
        <input
          type="file"
          accept="image/*"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
      </div>

      <div className="mt-6 text-center">
        <button
          onClick={handleVerify}
          disabled={!file || loading}
          className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Verifying..." : "Verify Image"}
        </button>
      </div>

      {result && (
        <div
          className={`mt-8 p-6 rounded-xl ${
            result.is_joyuri
              ? "bg-green-50 border border-green-200"
              : "bg-red-50 border border-red-200"
          }`}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold">
              {result.is_joyuri ? "Match Found!" : "No Match"}
            </h3>
            <span
              className={`text-2xl font-bold ${
                result.is_joyuri ? "text-green-600" : "text-red-600"
              }`}
            >
              {(result.confidence * 100).toFixed(1)}%
            </span>
          </div>
          <div className="space-y-2 text-sm text-gray-600">
            <p>
              <strong>Faces detected:</strong> {result.faces_detected}
            </p>
            <p>
              <strong>Message:</strong> {result.message}
            </p>
          </div>

          <div className="mt-4">
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  result.is_joyuri ? "bg-green-500" : "bg-red-400"
                }`}
                style={{ width: `${result.confidence * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
