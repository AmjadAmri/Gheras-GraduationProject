import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import type { StoryGenerationProgress } from "../../types/story";
import { Card } from "../../components/ui/Card";
import { ProgressBar } from "../../components/ui/ProgressBar";
import { Modal } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import {
  Check,
  AlertCircle,
  PenLine,
  Image,
  Mic,
  BookOpen,
  Clock,
  RefreshCw,
  Lightbulb,
} from "lucide-react";
import { cn } from "../../lib/cn";

type GenerationPayload = {
  childId: number;
  storyType: string;
  artStyle: string;
  targetBehavior: string;
  customBehavior?: string;
};

const generationSteps = [
  { id: "queued", label: "استلام الطلب", icon: BookOpen },
  { id: "writing", label: "كتابة القصة", icon: PenLine },
  { id: "initial_assets", label: "تجهيز الصور", icon: Image },
  { id: "background", label: "تجهيز الصوت", icon: Mic },
];

const funFacts = [
  { emoji: "📚", text: "القراءة للأطفال 20 دقيقة يومياً تعزز مهاراتهم اللغوية بشكل كبير" },
  { emoji: "🧠", text: "القصص تساعد الأطفال على تطوير الذكاء العاطفي والتعاطف" },
  { emoji: "🌟", text: "الأطفال الذين يقرؤون بانتظام يتفوقون أكاديمياً" },
  { emoji: "💡", text: "القصص المخصصة تجعل الطفل يشعر أنه بطل حقيقي" },
  { emoji: "🎨", text: "الصور في القصص تنمي خيال الطفل وإبداعه" },
  { emoji: "❤️", text: "وقت القراءة مع طفلك يقوي الرابطة العاطفية بينكما" },
  { emoji: "🦋", text: "تعلم السلوكيات من خلال القصص أكثر فعالية من التعليم المباشر" },
  { emoji: "🌈", text: "كل قصة يتم توليدها خصيصاً لطفلك بناءً على عمره واهتماماته" },
];

const TIMEOUT_MS = 5 * 60 * 1000;

function getInitialTarget(progress: StoryGenerationProgress | null) {
  if (!progress) return 3;

  return Math.max(
    1,
    Math.min(3, progress.totalPages || progress.initialPagesTarget || 3)
  );
}

function areInitialPagesReady(progress: StoryGenerationProgress | null) {
  if (!progress) return false;

  const target = getInitialTarget(progress);

  return (
    progress.status === "ready" &&
    progress.pagesWithImages >= target &&
    progress.pagesWithAudio >= target
  );
}

export function StoryGeneratingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const payload = (location.state as GenerationPayload | null) || null;

  const [storyId, setStoryId] = useState<number | null>(null);
  const [progressData, setProgressData] =
    useState<StoryGenerationProgress | null>(null);
  const [failed, setFailed] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [currentFactIndex, setCurrentFactIndex] = useState(0);

  const startedRef = useRef(false);
  const factTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!payload) {
      navigate("/create-story", { replace: true });
      return;
    }

    if (
      !payload.childId ||
      !payload.storyType ||
      !payload.artStyle ||
      !payload.targetBehavior
    ) {
      navigate("/create-story", { replace: true });
      return;
    }

    if (
      payload.targetBehavior === "other" &&
      !(payload.customBehavior || "").trim()
    ) {
      navigate("/create-story", { replace: true });
    }
  }, [payload, navigate]);

  useEffect(() => {
    if (!payload) return;
    if (startedRef.current) return;

    startedRef.current = true;

    api
      .post<StoryGenerationProgress>("/stories/", payload)
      .then((res) => {
        setStoryId(res.id);
        setProgressData(res);
      })
      .catch((err) => {
        setFailed(true);
        setErrorMessage(
          err instanceof Error ? err.message : "تعذر بدء إنشاء القصة"
        );
        setErrorModalOpen(true);
      });
  }, [payload]);

  useEffect(() => {
    factTimerRef.current = setInterval(() => {
      setCurrentFactIndex((prev) => (prev + 1) % funFacts.length);
    }, 8000);

    return () => {
      if (factTimerRef.current) clearInterval(factTimerRef.current);
    };
  }, []);

  useEffect(() => {
    if (!storyId) return;

    timeoutRef.current = setTimeout(() => {
      setTimedOut(true);
      setErrorModalOpen(true);
    }, TIMEOUT_MS);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [storyId]);

  useEffect(() => {
    if (!storyId) return;

    const interval = window.setInterval(async () => {
      try {
        const res = await api.get<StoryGenerationProgress>(
          `/stories/${storyId}/status/`
        );

        setProgressData(res);

        if (res.status === "failed") {
          window.clearInterval(interval);

          if (timeoutRef.current) clearTimeout(timeoutRef.current);
          if (factTimerRef.current) clearInterval(factTimerRef.current);

          setFailed(true);
          setErrorMessage("تعذر إنشاء القصة");
          setErrorModalOpen(true);
          return;
        }

        if (areInitialPagesReady(res)) {
          window.clearInterval(interval);

          if (timeoutRef.current) clearTimeout(timeoutRef.current);
          if (factTimerRef.current) clearInterval(factTimerRef.current);

          navigate(`/stories/${res.id}`, { replace: true });
        }
      } catch {
        // تجاهل أخطاء polling المؤقتة حتى لا تتوقف الصفحة بسبب انقطاع بسيط
      }
    }, 2000);

    return () => window.clearInterval(interval);
  }, [storyId, navigate]);

  const activeStepIndex = useMemo(() => {
    if (!progressData) return 0;

    switch (progressData.stage) {
      case "queued":
        return 0;
      case "writing":
      case "structuring":
        return 1;
      case "initial_assets":
        return 2;
      case "finalizing":
      case "background":
      case "complete":
        return 3;
      default:
        return 0;
    }
  }, [progressData]);

  const progressPercent = useMemo(() => {
    if (!progressData) return 5;

    const target = getInitialTarget(progressData);

    if (progressData.status === "queued") return 8;
    if (progressData.status === "generating_story") return 28;

    if (progressData.status === "generating_images") {
      const imageRatio = Math.min(progressData.pagesWithImages / target, 1);
      const audioRatio = Math.min(progressData.pagesWithAudio / target, 1);

      return Math.round(35 + ((imageRatio + audioRatio) / 2) * 55);
    }

    if (areInitialPagesReady(progressData)) return 100;
    if (progressData.status === "ready") return 95;
    if (progressData.status === "failed") return 100;

    return 12;
  }, [progressData]);

  const currentFact = funFacts[currentFactIndex];

  const statusMessage = useMemo(() => {
    if (!progressData) {
      return "نبدأ الآن في كتابة القصة";
    }

    const target = getInitialTarget(progressData);

    if (areInitialPagesReady(progressData)) {
      return "الصفحات الأولى جاهزة للقراءة";
    }

    if (progressData.status === "ready") {
      return `ننتظر اكتمال الصوت للصفحات الأولى ${progressData.pagesWithAudio}/${target}`;
    }

    return progressData.message || "انتظر قليلاً تَبقّى القليل لإنشاء قصتك الفريدة";
  }, [progressData]);

  const handleRetry = () => {
    navigate("/create-story");
  };

  const initialTarget = getInitialTarget(progressData);
  const initialReady = areInitialPagesReady(progressData);

  const imageProgressPercent = progressData
    ? Math.round(
        (Math.min(progressData.pagesWithImages, initialTarget) / initialTarget) *
          100
      )
    : 0;

  const audioProgressPercent = progressData
    ? Math.round(
        (Math.min(progressData.pagesWithAudio, initialTarget) / initialTarget) *
          100
      )
    : 0;

  return (
    <div className="flex items-center justify-center min-h-[70vh]">
      <Modal open={errorModalOpen} onClose={() => setErrorModalOpen(false)}>
        <div className="text-center py-2">
          <div className="mx-auto h-16 w-16 rounded-full bg-red-50 flex items-center justify-center mb-4">
            {timedOut ? (
              <Clock className="h-8 w-8 text-amber-500" />
            ) : (
              <AlertCircle className="h-8 w-8 text-red-500" />
            )}
          </div>

          <h3 className="text-lg font-bold text-gray-900 mb-2">
            {timedOut ? "استغرق الأمر وقتاً طويلاً" : "حدث خطأ!"}
          </h3>

          <p className="text-sm text-gray-500 mb-6">
            {timedOut
              ? "يبدو أن إنشاء القصة يستغرق أكثر من المتوقع. يمكنك المحاولة مرة أخرى."
              : errorMessage || "لم نتمكن من إنشاء القصة. يرجى المحاولة مرة أخرى."}
          </p>

          <div className="flex items-center justify-center gap-3">
            <Button onClick={handleRetry}>
              <RefreshCw className="h-4 w-4" />
              المحاولة مرة أخرى
            </Button>

            <Button variant="secondary" onClick={() => navigate("/")}>
              الرئيسية
            </Button>
          </div>
        </div>
      </Modal>

      <Card className="w-full max-w-xl text-center">
        <div className="mb-6">
          <div className="mx-auto h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center">
            <div className="h-14 w-14 rounded-full border-4 border-primary/20 border-t-sidebar animate-spin" />
          </div>
        </div>

        <h2 className="text-xl font-bold text-gray-900 mb-2">
          جاري إنشاء القصة
        </h2>

        <p className="text-sm text-gray-500 mb-6">{statusMessage}</p>

        <div className="mb-6">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-500">التقدم</span>
            <span className="font-semibold text-sidebar">
              {progressPercent}%
            </span>
          </div>

          <ProgressBar value={progressPercent} color="bg-sidebar" />

          {progressData && (
            <div className="mt-4 space-y-4 text-start">
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-gray-500">تجهيز الصور</span>
                  <span className="font-semibold text-sidebar">
                    {Math.min(progressData.pagesWithImages, initialTarget)}/
                    {initialTarget}
                  </span>
                </div>

                <ProgressBar
                  value={imageProgressPercent}
                  color="bg-sidebar"
                />
              </div>

              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-gray-500">تجهيز الصوت</span>
                  <span className="font-semibold text-primary">
                    {Math.min(progressData.pagesWithAudio, initialTarget)}/
                    {initialTarget}
                  </span>
                </div>

                <ProgressBar
                  value={audioProgressPercent}
                  color="bg-primary"
                />
              </div>

              <div className="text-xs text-gray-500 text-center">
                <span>إجمالي الصفحات: {progressData.totalPages || "..."}</span>

                <span className="mx-2">•</span>

                <span>
                  الصفحات الأولى: {initialReady ? "جاهزة للقراءة" : "قيد التجهيز"}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-3 text-start mb-6">
          {generationSteps.map((step, index) => {
            const isCompleted =
              index < activeStepIndex ||
              (step.id === "background" && progressData && progressData.pagesWithAudio >= initialTarget);

            const isActive =
              index === activeStepIndex && progressData?.status !== "failed"||
              (step.id === "background" &&
              progressData &&
              progressData.pagesWithAudio < initialTarget);

            return (
              <div
                key={step.id}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-4 py-3 transition-colors",
                  isActive && "bg-primary/5",
                  isCompleted && "bg-emerald-50"
                )}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full transition-colors",
                    isCompleted && "bg-primary text-white",
                    isActive && "bg-sidebar text-white",
                    !isCompleted && !isActive && "bg-gray-200 text-gray-400"
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <step.icon className="h-4 w-4" />
                  )}
                </div>

                <span
                  className={cn(
                    "text-sm font-medium",
                    isActive && "text-sidebar",
                    isCompleted && "text-primary",
                    !isActive && !isCompleted && "text-gray-400"
                  )}
                >
                  {step.label}
                </span>

                {isActive && (
                  <div className="ms-auto">
                    <div className="h-4 w-4 rounded-full border-2 border-sidebar border-t-transparent animate-spin" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {!failed && !timedOut && (
          <div className="rounded-xl bg-accent-gold/10 border border-accent-gold/20 p-4 text-start">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-gold/20">
                <Lightbulb className="h-4 w-4 text-amber-600" />
              </div>

              <div className="min-w-0">
                <p className="text-xs font-medium text-amber-700 mb-1">
                  هل تعلم؟
                </p>

                <p className="text-sm text-gray-700 leading-relaxed transition-opacity duration-500">
                  <span className="me-1">{currentFact.emoji}</span>
                  {currentFact.text}
                </p>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}