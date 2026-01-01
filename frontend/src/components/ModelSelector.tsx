"use client";

import { useState, useEffect, useRef } from "react";
import {
  listModels,
  getCurrentModel,
  setCurrentModel,
  loadModelStream,
  type ModelInfo,
} from "@/lib/api";

interface ModelSelectorProps {
  onModelChange?: (modelId: string) => void;
  onIndexRequest?: (modelId: string, modelName: string) => void;
}

const FAMILY_LABELS: Record<string, string> = {
  openai_clip: "OpenAI CLIP",
  openclip: "OpenCLIP",
  siglip: "SigLIP",
};

export function ModelSelector({ onModelChange, onIndexRequest }: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [currentModel, setCurrentModelState] = useState<string>("");
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function fetchModels() {
      try {
        const [modelList, current] = await Promise.all([
          listModels(),
          getCurrentModel(),
        ]);
        setModels(modelList);
        setCurrentModelState(current.model_id);
      } catch (error) {
        console.error("Failed to fetch models:", error);
      }
    }
    fetchModels();
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const refreshModels = async () => {
    try {
      const modelList = await listModels();
      setModels(modelList);
    } catch (error) {
      console.error("Failed to refresh models:", error);
    }
  };

  const handleSelectModel = async (modelId: string) => {
    if (modelId === currentModel) {
      setIsOpen(false);
      return;
    }

    const model = models.find((m) => m.id === modelId);
    if (!model) return;

    setLoading(true);
    setIsOpen(false);

    if (!model.is_loaded) {
      setLoadingMessage("Downloading model...");
      const es = loadModelStream(modelId, (data) => {
        if (data.status === "complete") {
          es.close();
          completeModelChange(modelId, model.is_indexed);
        } else if (data.status === "error") {
          es.close();
          setLoading(false);
          setLoadingMessage("");
          console.error("Model load error:", data.error);
        }
      });
      return;
    }

    await completeModelChange(modelId, model.is_indexed);
  };

  const completeModelChange = async (modelId: string, isIndexed: boolean) => {
    try {
      await setCurrentModel(modelId);
      setCurrentModelState(modelId);
      await refreshModels();

      if (!isIndexed) {
        const model = models.find((m) => m.id === modelId);
        if (model && onIndexRequest) {
          onIndexRequest(modelId, model.name);
        }
      }

      onModelChange?.(modelId);
    } catch (error) {
      console.error("Failed to set model:", error);
    } finally {
      setLoading(false);
      setLoadingMessage("");
    }
  };

  const currentModelInfo = models.find((m) => m.id === currentModel);
  const groupedModels = models.reduce((acc, model) => {
    if (!acc[model.family]) acc[model.family] = [];
    acc[model.family].push(model);
    return acc;
  }, {} as Record<string, ModelInfo[]>);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        className="flex items-center gap-2 px-3 py-3 text-sm border border-gray-300 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-50 min-w-[160px]"
      >
        {loading ? (
          <span className="text-gray-500">{loadingMessage || "Loading..."}</span>
        ) : (
          <>
            <span className="truncate flex-1 text-left">
              {currentModelInfo?.name || "Select Model"}
            </span>
            <svg
              className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </>
        )}
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-80 bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-y-auto right-0">
          {Object.entries(groupedModels).map(([family, familyModels]) => (
            <div key={family}>
              <div className="px-3 py-2 text-xs font-semibold text-gray-500 bg-gray-50 sticky top-0">
                {FAMILY_LABELS[family] || family}
              </div>
              {familyModels.map((model) => (
                <button
                  key={model.id}
                  onClick={() => handleSelectModel(model.id)}
                  className={`w-full px-3 py-2 text-left hover:bg-purple-50 transition-colors ${
                    model.id === currentModel ? "bg-purple-100" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{model.name}</span>
                    <div className="flex items-center gap-1.5">
                      {model.is_indexed && (
                        <span className="text-xs px-1.5 py-0.5 bg-green-100 text-green-700 rounded">
                          {model.indexed_count} imgs
                        </span>
                      )}
                      {!model.is_indexed && (
                        <span className="text-xs px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded">
                          Not indexed
                        </span>
                      )}
                      {model.is_loaded && (
                        <span
                          className="w-2 h-2 bg-green-500 rounded-full"
                          title="Model loaded in memory"
                        />
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{model.description}</p>
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
