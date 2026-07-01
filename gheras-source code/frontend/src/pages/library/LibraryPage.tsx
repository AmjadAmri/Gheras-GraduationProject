import { useState, useEffect, useMemo } from "react";
import { api } from "../../lib/api";
import type { Story, ConfigResponse } from "../../types/story";
import { useChildren } from "../../context/ChildrenContext";
import { PageHeader } from "../../components/PageHeader";
import { StoryCard } from "../../components/StoryCard";
import { Spinner } from "../../components/ui/Spinner";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { BookOpen, Search, X } from "lucide-react";

export function LibraryPage() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const { children } = useChildren();

  const [config, setConfig] = useState<ConfigResponse | null>(null);

  const [searchText, setSearchText] = useState("");
  const [selectedChild, setSelectedChild] = useState("");
  const [selectedBehavior, setSelectedBehavior] = useState("");
  const [selectedGenre, setSelectedGenre] = useState("");

  useEffect(() => {
    Promise.all([
      api.get<Story[]>("/stories/"),
      api.get<ConfigResponse>("/config/"),
    ])
      .then(([storiesData, configData]) => {
        setStories(storiesData);
        setConfig(configData);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filteredStories = useMemo(() => {
    return stories.filter((story) => {
      if (searchText && !story.title.toLowerCase().includes(searchText.toLowerCase())) {
        return false;
      }
      if (selectedChild && story.childId !== Number(selectedChild)) {
        return false;
      }
      if (selectedBehavior && story.targetBehavior !== selectedBehavior) {
        return false;
      }
      if (selectedGenre && story.storyType !== selectedGenre) {
        return false;
      }
      return true;
    });
  }, [stories, searchText, selectedChild, selectedBehavior, selectedGenre]);

  const hasActiveFilters = searchText || selectedChild || selectedBehavior || selectedGenre;

  const clearFilters = () => {
    setSearchText("");
    setSelectedChild("");
    setSelectedBehavior("");
    setSelectedGenre("");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  const behaviorOptions = (config?.behaviors ?? []).map((b) => ({
    value: b.key,
    label: b.label,
  }));

  const genreOptions = (config?.genres ?? []).map((g) => ({
    value: g.key,
    label: g.label,
  }));

  const childOptions = children.map((c) => ({
    value: c.id.toString(),
    label: c.name,
  }));

  return (
    <div>
      <PageHeader title="المكتبة" description="جميع القصص التي تم إنشاؤها" />

      {/* Search & Filters */}
      <div className="mb-6 space-y-3">
        <div className="relative">
          <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
          <input
            type="text"
            placeholder="ابحث عن قصة..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white ps-10 pe-4 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <Select
              options={[{ value: "", label: "كل الأطفال" }, ...childOptions]}
              value={selectedChild}
              onChange={(e) => setSelectedChild(e.target.value)}
            />
          </div>
          <div className="flex-1">
            <Select
              options={[{ value: "", label: "كل السلوكيات" }, ...behaviorOptions]}
              value={selectedBehavior}
              onChange={(e) => setSelectedBehavior(e.target.value)}
            />
          </div>
          <div className="flex-1">
            <Select
              options={[{ value: "", label: "كل الأنواع" }, ...genreOptions]}
              value={selectedGenre}
              onChange={(e) => setSelectedGenre(e.target.value)}
            />
          </div>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 transition-colors cursor-pointer shrink-0"
            >
              <X className="h-4 w-4" />
              مسح
            </button>
          )}
        </div>
      </div>

      {stories.length > 0 ? (
        filteredStories.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredStories.map((story) => (
              <StoryCard key={story.id} story={story} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center min-h-[40vh] text-center">
            <Search className="h-10 w-10 text-gray-300 mb-3" />
            <h3 className="text-lg font-semibold text-gray-900 mb-1">لا توجد نتائج</h3>
            <p className="text-sm text-gray-500">جرب تغيير معايير البحث</p>
          </div>
        )
      ) : (
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gray-100 mb-4">
            <BookOpen className="h-10 w-10 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">لا توجد قصص بعد</h3>
          <p className="text-sm text-gray-500">ابدأ بإنشاء أول قصة لطفلك!</p>
        </div>
      )}
    </div>
  );
}
