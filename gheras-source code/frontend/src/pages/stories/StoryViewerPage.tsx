import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import type { Story, StoryPage } from "../../types/story";
import { Button } from "../../components/ui/Button";
import { Spinner } from "../../components/ui/Spinner";
import {
  ChevronLeft,
  ChevronRight,
  Play,
  Pause,
  Download,
  Loader2,
  ArrowRight,
  Sparkles,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { cn } from "../../lib/cn";

const BEHAVIOR_PROMPTS: Record<string, { question: string; emoji: string }> = {
  courage: { question: "هل ستكون شجاعاً اليوم؟", emoji: "🦁" },
  kindness: { question: "هل ستكون لطيفاً مع الآخرين؟", emoji: "💖" },
  sharing: { question: "هل ستشارك أشياءك مع أصدقائك؟", emoji: "🤝" },
  honesty: { question: "هل ستقول الحقيقة دائماً؟", emoji: "⭐" },
  responsibility: { question: "هل ستتحمل مسؤولياتك اليوم؟", emoji: "📋" },
  patience: { question: "هل ستتحلى بالصبر؟", emoji: "🕐" },
  respect: { question: "هل ستحترم الآخرين؟", emoji: "👑" },
  gratitude: { question: "هل ستشكر من حولك؟", emoji: "🎁" },
};

type PdfStatusResponse = {
  status: "pending" | "generating" | "ready" | "failed";
  progress: number;
  ready: boolean;
  pdfUrl?: string;
  error?: string;
};

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function safeFileTitle(title: string) {
  return (
    title.replace(/[^a-zA-Z0-9\u0600-\u06FF\s-]/g, "").trim() || "story"
  );
}

export function StoryViewerPage() {
  const { storyId } = useParams();
  const navigate = useNavigate();

  const [story, setStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);

  const readStartRef = useRef(Date.now());
  const readingLogStartedRef = useRef(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioCacheRef = useRef<Record<number, string>>({});

  const [isPlaying, setIsPlaying] = useState(false);
  const [isAudioLoading, setIsAudioLoading] = useState(false);

  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadMessage, setDownloadMessage] = useState("");
  const [downloadError, setDownloadError] = useState("");

  const [taskCompleted, setTaskCompleted] = useState(false);
  const [taskResponse, setTaskResponse] = useState<string | null>(null);

  const loadStory = useCallback(async () => {
    if (!storyId) return;

    const data = await api.get<Story>(`/stories/${storyId}/`);
    setStory(data);
  }, [storyId]);

  useEffect(() => {
    if (!storyId) return;

    readStartRef.current = Date.now();
    readingLogStartedRef.current = false;

    loadStory()
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [storyId, loadStory]);

  useEffect(() => {
    if (!story || readingLogStartedRef.current) return;

    readingLogStartedRef.current = true;

    api
      .post("/reading-logs/", {
        childId: story.childId,
        storyId: story.id,
        timeSpent: 0,
        finished: false,
      })
      .catch(() => {});
  }, [story?.id, story]);

  useEffect(() => {
    if (!storyId || !story) return;

    const needsRefresh =
      story.pages.some((page) => !page.illustrationUrl) ||
      !story.coverUrl;

    if (!needsRefresh) return;

    const interval = window.setInterval(() => {
      loadStory().catch(() => {});
    }, 4000);

    return () => window.clearInterval(interval);
  }, [storyId, story, loadStory]);

  const pages = story?.pages || [];
  const totalPages = pages.length;
  const page = pages[currentPage];

  const stopPlayback = useCallback(() => {
    const audio = audioRef.current;

    if (audio) {
      audio.pause();
    }

    setIsPlaying(false);
  }, []);

  const refreshStory = useCallback(async () => {
    if (!storyId) return null;

    const latestStory = await api.get<Story>(`/stories/${storyId}/`);
    setStory(latestStory);

    return latestStory;
  }, [storyId]);

  const getAudioForPage = useCallback(
    async (storyPage?: StoryPage | null) => {
      if (!storyId || !storyPage?.pageNumber) return "";

      if (audioCacheRef.current[storyPage.pageNumber]) {
        return audioCacheRef.current[storyPage.pageNumber];
      }

      if (storyPage.audioUrl) {
        audioCacheRef.current[storyPage.pageNumber] = storyPage.audioUrl;
        return storyPage.audioUrl;
      }

      const res = await api.get<{ audio: string; cached?: boolean }>(
        `/stories/${storyId}/audio/${storyPage.pageNumber}/`
      );

      if (res.audio) {
        audioCacheRef.current[storyPage.pageNumber] = res.audio;
      }

      return res.audio || "";
    },
    [storyId]
  );

  const preloadAudio = useCallback(
    async (storyPage?: StoryPage | null) => {
      try {
        await getAudioForPage(storyPage);
      } catch {
        // ignore
      }
    },
    [getAudioForPage]
  );

  const playCurrentPageAudio = useCallback(async () => {
    if (!storyId || !page?.pageNumber) return;

    try {
      setIsAudioLoading(true);

      let audioUrl = await getAudioForPage(page);

      if (!audioUrl) {
        const latestStory = await refreshStory();

        const latestPage = latestStory?.pages?.find(
          (item) => item.pageNumber === page.pageNumber
        );

        audioUrl = await getAudioForPage(latestPage || page);
      }

      if (!audioUrl || !audioRef.current) {
        setIsPlaying(false);
        return;
      }

      audioRef.current.src = audioUrl;

      await audioRef.current.play();
      setIsPlaying(true);
    } catch {
      setIsPlaying(false);
    } finally {
      setIsAudioLoading(false);
    }
  }, [storyId, page, getAudioForPage, refreshStory]);

  const togglePlayback = useCallback(async () => {
    if (isPlaying) {
      stopPlayback();
      return;
    }

    await playCurrentPageAudio();
  }, [isPlaying, stopPlayback, playCurrentPageAudio]);

  useEffect(() => {
    stopPlayback();
  }, [currentPage, stopPlayback]);

  const nextPageNumber = pages[currentPage + 1]?.pageNumber;

  useEffect(() => {
    const nextPage = pages.find((item) => item.pageNumber === nextPageNumber);
    preloadAudio(nextPage).catch(() => {});
  }, [nextPageNumber, preloadAudio]);

  useEffect(() => {
    const audio = audioRef.current;

    if (!audio) return;

    const handleEnded = () => setIsPlaying(false);
    const handlePause = () => setIsPlaying(false);
    const handlePlay = () => setIsPlaying(true);
    const handleError = () => setIsPlaying(false);

    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("error", handleError);

    return () => {
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("error", handleError);
    };
  }, []);

  useEffect(() => {
    return () => {
      audioRef.current?.pause();
    };
  }, []);

  const pollPdfUntilReady = useCallback(
    async (storyIdValue: number) => {
      for (let attempt = 0; attempt < 180; attempt += 1) {
        const status = await api.get<PdfStatusResponse>(
          `/stories/${storyIdValue}/pdf-status/`
        );

        const progress = Math.max(1, Math.min(99, status.progress || 1));
        setDownloadProgress(progress);

        if (status.status === "failed") {
          throw new Error(status.error || "فشل إنشاء ملف PDF");
        }

        if (status.ready || status.status === "ready") {
          setDownloadProgress(95);
          return status;
        }

        await wait(1000);
      }

      throw new Error("استغرق تجهيز ملف PDF وقتاً طويلاً");
    },
    []
  );

  const handleDownload = async () => {
    if (!story || downloading) return;

    setDownloading(true);
    setDownloadProgress(1);
    setDownloadMessage("جاري تجهيز ملف PDF...");
    setDownloadError("");

    try {
      const generateResponse = await api.post<PdfStatusResponse>(
        `/stories/${story.id}/generate-pdf/`
      );

      setDownloadProgress(generateResponse.progress || 5);

      if (generateResponse.status === "failed") {
        throw new Error(generateResponse.error || "فشل تجهيز ملف PDF");
      }

      if (!generateResponse.ready && generateResponse.status !== "ready") {
        await pollPdfUntilReady(story.id);
      } else {
        setDownloadProgress(95);
      }

      setDownloadMessage("جاري تنزيل الملف...");

      const blob = await api.getBlobWithProgress(
        `/stories/${story.id}/download-pdf/`,
        (progress) => {
          setDownloadProgress(Math.max(95, progress));
        }
      );

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");

      a.href = url;
      a.download = `story-${safeFileTitle(story.title)}.pdf`;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      URL.revokeObjectURL(url);

      setDownloadProgress(100);
      setDownloadMessage("تم تحميل ملف PDF بنجاح");

      await loadStory();
    } catch (error) {
      console.error("PDF download failed:", error);

      setDownloadError(
        error instanceof Error
          ? error.message
          : "فشل تحميل ملف PDF، يرجى المحاولة مرة أخرى"
      );

      setDownloadMessage("تعذر تحميل ملف PDF");
      loadStory().catch(() => {});
    } finally {
      setTimeout(() => {
        setDownloading(false);
        setDownloadProgress(0);
        setDownloadMessage("");
      }, 1400);
    }
  };

  const handleTaskResponse = async (response: "yes" | "try") => {
    if (!story) return;

    setTaskResponse(response);

    const timeSpent = Math.round((Date.now() - readStartRef.current) / 1000);

    await api
      .post("/tasks/", {
        childId: story.childId,
        storyId: story.id,
        behavior: story.targetBehavior,
        response,
      })
      .catch(() => {});

    await api
      .post("/reading-logs/", {
        childId: story.childId,
        storyId: story.id,
        timeSpent,
        finished: true,
      })
      .catch(() => {});

    setTaskCompleted(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!story || !page) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          القصة غير موجودة
        </h2>
        <p className="text-gray-500 mb-4">لم نتمكن من العثور على هذه القصة</p>
        <Button onClick={() => navigate("/library")}>العودة للمكتبة</Button>
      </div>
    );
  }

  const paragraphs =
    page.narrationText
      ?.split(/\n+/)
      .filter((p) => p.trim().length > 0) ?? [];

  const isLastPage = currentPage === totalPages - 1;
  const showTaskCard = isLastPage && !taskCompleted;

  const behaviorPrompt =
    BEHAVIOR_PROMPTS[story.targetBehavior] || BEHAVIOR_PROMPTS.courage;

  const goNext = () => setCurrentPage((p) => Math.min(p + 1, totalPages - 1));
  const goPrev = () => setCurrentPage((p) => Math.max(p - 1, 0));

  return (
    <div>
      <audio ref={audioRef} preload="auto" />

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <ArrowRight className="h-5 w-5" />
          </button>

          <div>
            <h1 className="text-lg sm:text-xl font-bold text-gray-900">
              {story.title}
            </h1>

            <p className="text-sm text-gray-500">
              قصة {story.childName} · {totalPages} صفحات
            </p>
          </div>
        </div>

        <div className="ps-11 sm:ps-0">
          <div className="flex items-center gap-2">
            <Button
              variant={isPlaying ? "primary" : "secondary"}
              size="sm"
              onClick={togglePlayback}
              disabled={isAudioLoading}
            >
              {isAudioLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : isPlaying ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4" />
              )}

              <span className="hidden sm:inline">
                {isAudioLoading
                  ? "جاري التحميل..."
                  : isPlaying
                    ? "إيقاف"
                    : "استماع"}
              </span>
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownload}
              disabled={downloading}
              className="relative overflow-hidden"
            >
              {downloading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}

              <span className="hidden sm:inline">
                {downloading ? `${downloadProgress}%` : "تحميل PDF"}
              </span>
            </Button>
          </div>

          {downloading && (
            <div className="mt-3 w-64 max-w-full">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-sidebar transition-all duration-300"
                  style={{ width: `${downloadProgress}%` }}
                />
              </div>

              <p className="text-xs text-gray-500 mt-1">
                {downloadMessage || "جاري تجهيز ملف PDF..."}
              </p>
            </div>
          )}

          {downloadError && !downloading && (
            <div className="mt-3 flex items-start gap-2 rounded-lg bg-red-50 border border-red-100 px-3 py-2 text-xs text-red-600">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{downloadError}</span>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-2 md:min-h-[500px]">
          <div className="bg-gray-50 aspect-square md:aspect-auto">
            <img
              src={page.illustrationUrl}
              alt={`صفحة ${page.pageNumber}`}
              className="h-full w-full object-cover"
            />
          </div>

          <div className="flex flex-col justify-center p-5 sm:p-8 md:p-12">
            <div className="space-y-3">
              {paragraphs.map((para, idx) => (
                <p
                  key={idx}
                  className={cn(
                    "text-lg leading-relaxed transition-all duration-300 text-gray-800"
                  )}
                >
                  {para}
                </p>
              ))}
            </div>

            <p className="mt-6 text-sm text-gray-400">
              صفحة {currentPage + 1} من {totalPages}
            </p>
          </div>
        </div>
      </div>

      {showTaskCard && (
        <div className="mt-6 bg-gradient-to-br from-primary/5 to-accent-gold/10 rounded-2xl border-2 border-primary/20 p-8 text-center">
          <div className="text-5xl mb-4">{behaviorPrompt.emoji}</div>

          <Sparkles className="h-6 w-6 text-accent-gold mx-auto mb-2" />

          <h3 className="text-xl font-bold text-gray-900 mb-2">
            أحسنت! أنهيت القصة
          </h3>

          <p className="text-lg text-gray-700 mb-6">
            {behaviorPrompt.question}
          </p>

          <div className="flex items-center justify-center gap-4">
            <Button
              size="lg"
              onClick={() => handleTaskResponse("yes")}
              disabled={taskResponse !== null}
            >
              <CheckCircle className="h-5 w-5" />
              نعم!
            </Button>

            <Button
              variant="secondary"
              size="lg"
              onClick={() => handleTaskResponse("try")}
              disabled={taskResponse !== null}
            >
              سأحاول
            </Button>
          </div>
        </div>
      )}

      {taskCompleted && isLastPage && (
        <div className="mt-6 bg-green-50 rounded-2xl border border-green-200 p-6 text-center">
          <CheckCircle className="h-10 w-10 text-green-500 mx-auto mb-2" />

          <h3 className="text-lg font-bold text-green-800">ممتاز! 🎉</h3>

          <p className="text-green-700 mt-1">تم تسجيل قراءتك بنجاح</p>

          <Button
            variant="secondary"
            size="sm"
            className="mt-4"
            onClick={() => navigate("/library")}
          >
            العودة للمكتبة
          </Button>
        </div>
      )}

      <div className="flex items-center justify-center gap-4 mt-6">
        <button
          onClick={goNext}
          disabled={currentPage === totalPages - 1}
          className="rounded-full p-2 text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
        >
          <ChevronRight className="h-6 w-6" />
        </button>

        <div className="flex items-center gap-2">
          {pages.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentPage(idx)}
              className={cn(
                "h-2.5 rounded-full transition-all cursor-pointer",
                idx === currentPage
                  ? "w-8 bg-sidebar"
                  : "w-2.5 bg-gray-300 hover:bg-gray-400"
              )}
            />
          ))}
        </div>

        <button
          onClick={goPrev}
          disabled={currentPage === 0}
          className="rounded-full p-2 text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
        >
          <ChevronLeft className="h-6 w-6" />
        </button>
      </div>
    </div>
  );
}