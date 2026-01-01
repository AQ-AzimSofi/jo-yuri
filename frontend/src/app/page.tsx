"use client";

import { useState, useCallback } from "react";
import { searchImages, getImageUrl, listModels, type SearchResult } from "@/lib/api";
import { ImageGrid } from "@/components/ImageGrid";
import { ModelSelector } from "@/components/ModelSelector";
import { IndexingProgress } from "@/components/IndexingProgress";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [currentModel, setCurrentModel] = useState<string>("");
  const [indexingModel, setIndexingModel] = useState<{
    id: string;
    name: string;
  } | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await searchImages(query, 12, currentModel || undefined);
      setResults(response.results);
      setSearched(true);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleModelChange = useCallback(
    (modelId: string) => {
      setCurrentModel(modelId);
      if (searched && query.trim()) {
        setLoading(true);
        searchImages(query, 12, modelId)
          .then((response) => setResults(response.results))
          .catch((error) => console.error("Search failed:", error))
          .finally(() => setLoading(false));
      }
    },
    [searched, query]
  );

  const handleIndexRequest = useCallback((modelId: string, modelName: string) => {
    setIndexingModel({ id: modelId, name: modelName });
  }, []);

  const handleIndexComplete = useCallback(async () => {
    await listModels();
    if (searched && query.trim() && indexingModel) {
      setLoading(true);
      searchImages(query, 12, indexingModel.id)
        .then((response) => setResults(response.results))
        .catch((error) => console.error("Search failed:", error))
        .finally(() => setLoading(false));
    }
  }, [searched, query, indexingModel]);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Semantic Image Search
        </h1>
        <p className="text-gray-600">
          Search Jo Yuri images by description (e.g., &quot;smiling&quot;, &quot;concert&quot;, &quot;close up&quot;)
        </p>
      </div>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter search query..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            suppressHydrationWarning
          />
          <ModelSelector
            onModelChange={handleModelChange}
            onIndexRequest={handleIndexRequest}
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
      </form>

      {searched && (
        <div>
          <p className="text-sm text-gray-500 mb-4">
            Found {results.length} results for &quot;{query}&quot;
          </p>
          <ImageGrid
            images={results.map((r) => ({
              src: getImageUrl(r.filename),
              filename: r.filename,
              score: r.score,
            }))}
          />
        </div>
      )}

      {indexingModel && (
        <IndexingProgress
          modelId={indexingModel.id}
          modelName={indexingModel.name}
          onComplete={handleIndexComplete}
          onClose={() => setIndexingModel(null)}
        />
      )}
    </div>
  );
}
