import { useState, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useChildren } from "../../context/ChildrenContext";
import { useMultiStepForm } from "../../hooks/useMultiStepForm";
import { api } from "../../lib/api";
import type { ConfigResponse } from "../../types/story";
import { PageHeader } from "../../components/PageHeader";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Select } from "../../components/ui/Select";
import { Spinner } from "../../components/ui/Spinner";
import { StepIndicator } from "../../components/StepIndicator";
import { SelectableGrid } from "../../components/SelectableGrid";
import { artStylePreview } from "../../lib/formatters";
import {
  Compass,
  Sparkles,
  GraduationCap,
  Users,
  TreePine,
  Rocket,
  Shield,
  Heart,
  HandHeart,
  Star,
  ClipboardCheck,
  Clock,
  Crown,
  Gift,
  PenLine,
} from "lucide-react";

const iconMap: Record<string, React.ReactNode> = {
  Compass: <Compass className="h-6 w-6" />,
  Sparkles: <Sparkles className="h-6 w-6" />,
  GraduationCap: <GraduationCap className="h-6 w-6" />,
  Users: <Users className="h-6 w-6" />,
  TreePine: <TreePine className="h-6 w-6" />,
  Rocket: <Rocket className="h-6 w-6" />,
  Shield: <Shield className="h-6 w-6" />,
  Heart: <Heart className="h-6 w-6" />,
  HandHeart: <HandHeart className="h-6 w-6" />,
  Star: <Star className="h-6 w-6" />,
  ClipboardCheck: <ClipboardCheck className="h-6 w-6" />,
  Clock: <Clock className="h-6 w-6" />,
  Crown: <Crown className="h-6 w-6" />,
  Gift: <Gift className="h-6 w-6" />,
  PenLine: <PenLine className="h-6 w-6" />,
};

const steps = ["نوع القصة", "الأسلوب الفني", "السلوك المستهدف"];

const artStyleImages: Record<string, string> = {
  storybook: "/art-styles/storybook.webp",
  cartoon: "/art-styles/cartoon.webp",
  watercolor: "/art-styles/watercolor.webp",
  paper: "/art-styles/paper.webp",
  pixel: "/art-styles/pixel.webp",
  anime: "/art-styles/anime.webp",
};

export function CreateStoryPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { children } = useChildren();
  const { currentStep, next, back, isFirst, isLast } = useMultiStepForm(3);

  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [configLoading, setConfigLoading] = useState(true);

  const [childId, setChildId] = useState(searchParams.get("childId") || children[0]?.id?.toString() || "");
  const [storyTypeId, setStoryTypeId] = useState<string | null>(null);
  const [artStyleId, setArtStyleId] = useState<string | null>(null);
  const [behaviorId, setBehaviorId] = useState<string | null>(null);
  const [customBehavior, setCustomBehavior] = useState("");

  useEffect(() => {
    api.get<ConfigResponse>("/config/")
      .then(setConfig)
      .catch(() => {})
      .finally(() => setConfigLoading(false));
  }, []);

  const storyTypes = config?.genres ?? [];
  const artStyles = config?.styles ?? [];
  const behaviors = config?.behaviors ?? [];

  const behaviorOptions = useMemo(() => {
    const hasOther = behaviors.some((b) => b.key === "other");
    if (hasOther) return behaviors;
    return [
      ...behaviors,
      {
        key: "other",
        label: "أخرى",
        description: "اكتب السلوك الذي تريده يدويًا",
        icon: "PenLine",
      },
    ];
  }, [behaviors]);

  const invalidCustomBehaviorPattern = /(.)\1{3,}|[^\u0600-\u06FF\s،؟.!-]/;
  const isCustomBehaviorInvalid =
    behaviorId === "other" &&
    !!customBehavior.trim() &&
    invalidCustomBehaviorPattern.test(customBehavior.trim());

  const canNext =
    (currentStep === 0 && !!storyTypeId) ||
    (currentStep === 1 && !!artStyleId) ||
    (currentStep === 2 &&
      !!behaviorId &&
      (behaviorId !== "other" ||
        (!!customBehavior.trim() && !isCustomBehaviorInvalid)));

  const handleFinish = () => {
    if (!childId || !storyTypeId || !artStyleId || !behaviorId) return;

    if (behaviorId === "other" && !customBehavior.trim()) {
      window.alert("الرجاء كتابة السلوك المطلوب");
      return;
    }

    if (isCustomBehaviorInvalid) {
      window.alert("يرجى إدخال سلوك مفهوم باللغة العربية فقط");
      return;
    }

    navigate("/create-story/generating", {
      state: {
        childId: Number(childId),
        storyType: storyTypeId,
        artStyle: artStyleId,
        targetBehavior: behaviorId,
        customBehavior: behaviorId === "other" ? customBehavior.trim() : "",
      },
    });
  };

  if (configLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="w-full sm:max-w-3xl sm:mx-auto">
      <PageHeader title="إنشاء قصة جديدة" description="اختر تفاصيل القصة لطفلك" />

      <Card>
        <div className="mb-6">
          <Select
            label="اختر الطفل"
            options={children.map((c) => ({ value: c.id.toString(), label: c.name }))}
            value={childId}
            onChange={(e) => setChildId(e.target.value)}
          />
        </div>

        <StepIndicator steps={steps} currentStep={currentStep} className="mb-8" />

        <div className="mb-8">
          {currentStep === 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">اختر نوع القصة</h3>
              <SelectableGrid
                items={storyTypes.map((t) => ({
                  id: t.key,
                  label: t.label,
                  description: t.description,
                  icon: iconMap[t.icon],
                }))}
                selectedId={storyTypeId}
                onSelect={setStoryTypeId}
              />
            </div>
          )}


          {currentStep === 1 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4"> اختر الأسلوب الفني </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {artStyles.map((style) => {
                  const isSelected = style.key === artStyleId;

                  const imageSrc =
                    style.previewUrl ||
                    artStyleImages[style.key] ||
                    artStylePreview(style.key);

                  return (
                    <button
                      key={style.key}
                      type="button"
                      onClick={() => setArtStyleId(style.key)}
                      className={`group relative overflow-hidden rounded-2xl border-2 bg-white text-right transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${
                        isSelected
                          ? "border-primary ring-4 ring-primary/20 shadow-md"
                          : "border-gray-200 hover:border-primary/60"
                      }`}
                    >
                      <div className="relative h-40 w-full overflow-hidden bg-gray-100">
                        <img
                          src={imageSrc}
                          alt={style.label}
                          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                          loading="lazy"
                        />

                        <div className="absolute inset-0 bg-linear-to-t from-black/40 via-black/10 to-transparent" />
                      </div>

                      <div className="p-4">
                        <h4 className="text-base font-bold text-gray-900">
                          {style.label}
                        </h4>

                        {style.description && (
                          <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                            {style.description}
                          </p>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">اختر السلوك المستهدف</h3>

              <SelectableGrid
                items={behaviorOptions.map((b) => ({
                  id: b.key,
                  label: b.label,
                  description: b.description,
                  icon: iconMap[b.icon] || <PenLine className="h-6 w-6" />,
                }))}
                selectedId={behaviorId}
                onSelect={(id) => {
                  const wasOther = behaviorId === "other";
                  const nextIsOther = id === "other";
                  setBehaviorId(id);
                  if (wasOther && !nextIsOther) {
                    setCustomBehavior("");
                  }
                }}
                columns={2}
              />

              {behaviorId === "other" && (
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    اكتب السلوك الذي تريده
                  </label>
                  <input
                    type="text"
                    value={customBehavior}
                    onChange={(e) => setCustomBehavior(e.target.value)}
                    maxLength={30}
                    placeholder="مثال: الاستماع الجيد، التعاون مع الأشقاء..."
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    autoFocus
                  />
                  {isCustomBehaviorInvalid && (
                    <p className="mt-2 text-sm text-red-600"> يرجى إدخال سلوك مفهوم باللغة العربية فقط. </p>
                  )}
                  
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-between">
          <Button variant="secondary" onClick={back} disabled={isFirst}>
            السابق
          </Button>
          {isLast ? (
            <Button onClick={handleFinish} disabled={!canNext}>
              إنشاء القصة
            </Button>
          ) : (
            <Button onClick={next} disabled={!canNext}>
              التالي
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}
