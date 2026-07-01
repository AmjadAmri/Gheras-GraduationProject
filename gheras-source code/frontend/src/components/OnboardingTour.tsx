import { useState, useEffect, useRef, useCallback, type CSSProperties } from "react";
import { cn } from "../lib/cn";
import { Button } from "./ui/Button";
import { X, ChevronRight } from "lucide-react";

const ONBOARDING_KEY = "gheras_onboarding_seen";
const LOGIN_POPUP_KEY = "gheras_show_login_popup";

interface TourStep {
  target: string;
  title: string;
  description: string;
}

const tourSteps: TourStep[] = [
  {
    target: '[data-tour="children"]',
    title: "إضافة طفل",
    description: "ابدأ بإضافة طفلك هنا لتتمكن من إنشاء قصص مخصصة له",
  },
  {
    target: '[data-tour="create-story"]',
    title: "إنشاء قصة",
    description: "بعد إضافة طفل، اضغط هنا لإنشاء قصة جديدة مخصصة",
  },
];

export function OnboardingTour() {
  const [active, setActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [tooltipStyle, setTooltipStyle] = useState<CSSProperties>({});
  const [arrowStyle, setArrowStyle] = useState<CSSProperties>({});
  const [arrowSide, setArrowSide] = useState<"left" | "right">("right");
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const seen = localStorage.getItem(ONBOARDING_KEY);
    const shouldShowAfterLogin = sessionStorage.getItem(LOGIN_POPUP_KEY);

    if (!seen || shouldShowAfterLogin) {
      const timer = setTimeout(() => {
       setActive(true);
       sessionStorage.removeItem(LOGIN_POPUP_KEY);
      }, 800);

      return () => clearTimeout(timer);
    }
  }, []);

  const positionTooltip = useCallback(() => {
    const step = tourSteps[currentStep];
    const targetElement = document.querySelector(step.target);

    if (!targetElement) return;

    const rect = targetElement.getBoundingClientRect();
    const tooltipElement = tooltipRef.current;
    const tooltipWidth = tooltipElement?.offsetWidth || 320;
    const tooltipHeight = tooltipElement?.offsetHeight || 150;
    const gap = 18;

    const isTargetOnRightSide = rect.left > window.innerWidth / 2;

    let top = rect.top + rect.height / 2 - tooltipHeight / 2;
    let left = isTargetOnRightSide
      ? rect.left - tooltipWidth - gap
      : rect.right + gap;

    top = Math.max(16, Math.min(top, window.innerHeight - tooltipHeight - 16));
    left = Math.max(16, Math.min(left, window.innerWidth - tooltipWidth - 16));

    setTooltipStyle({
      top,
      left,
      width: tooltipWidth,
    });

    setArrowSide(isTargetOnRightSide ? "right" : "left");

    setArrowStyle({
      top: tooltipHeight / 2 - 8,
      [isTargetOnRightSide ? "right" : "left"]: -8,
    });
  }, [currentStep]);

  useEffect(() => {
    if (active) {
      setTimeout(positionTooltip, 50);
    }
  }, [active, positionTooltip]);

  useEffect(() => {
    if (!active) return;

    positionTooltip();
    
    // Retry positioning if target not found (DOM not ready yet)
    const step = tourSteps[currentStep];
    const targetElement = document.querySelector(step.target);
    if (!targetElement) {
      const retryTimer = setTimeout(positionTooltip, 300);
      return () => clearTimeout(retryTimer);
    }

    window.addEventListener("resize", positionTooltip);
    window.addEventListener("scroll", positionTooltip, true);

    return () => {
      window.removeEventListener("resize", positionTooltip);
      window.removeEventListener("scroll", positionTooltip, true);
    };
  }, [active, currentStep, positionTooltip]);

  useEffect(() => {
    if (!active) return;

    const step = tourSteps[currentStep];
    const targetElement = document.querySelector(step.target) as HTMLElement | null;

    if (targetElement) {
      targetElement.style.position = "relative";
      targetElement.style.zIndex = "60";
      targetElement.style.borderRadius = "12px";
      targetElement.style.boxShadow = "0 0 0 4px rgba(255, 255, 255, 0.25)";
      targetElement.style.backgroundColor = "rgba(255, 255, 255, 0.18)";
    }

    return () => {
      if (targetElement) {
        targetElement.style.zIndex = "";
        targetElement.style.boxShadow = "";
        targetElement.style.backgroundColor = "";
      }
    };
  }, [active, currentStep]);

  const dismiss = () => {
    setActive(false);
    localStorage.setItem(ONBOARDING_KEY, "true");
    sessionStorage.removeItem(LOGIN_POPUP_KEY);
  };

  const nextStep = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep((step) => step + 1);
    } else {
      dismiss();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep((step) => step - 1);
    }
  };

  if (!active) return null;

  const step = tourSteps[currentStep];
  const isLastStep = currentStep === tourSteps.length - 1;
  const isFirstStep = currentStep === 0;

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/45 backdrop-blur-[1px] transition-opacity duration-300"
        onClick={dismiss}
      />

      <div
        ref={tooltipRef}
        dir="rtl"
        className="fixed z-70 w-[320px] rounded-2xl border border-gray-100 bg-white p-5 shadow-2xl animate-tour-popup"
        style={tooltipStyle}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className={cn(
            "absolute h-4 w-4 rotate-45 bg-white border-gray-100",
            arrowSide === "right" ? "border-t border-r" : "border-b border-l"
          )}
          style={arrowStyle}
        />

        <button
          type="button"
          onClick={dismiss}
          className="absolute top-4 inset-e-4 rounded-full p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 cursor-pointer"
          aria-label="إغلاق"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="pe-8">
          <h4 className="mb-2 text-base font-bold leading-6 text-gray-900">
            {step.title}
          </h4>

          <p className="text-sm leading-7 text-gray-500">
            {step.description}
          </p>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <span className="text-sm text-gray-400">
            {currentStep + 1} / {tourSteps.length}
          </span>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={dismiss}
              className="text-sm text-gray-400 transition-colors hover:text-gray-600 cursor-pointer"
            >
              تخطي
            </button>

            {!isFirstStep && (
              <button
                type="button"
                onClick={prevStep}
                className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 cursor-pointer"
                aria-label="السابق"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            )}

            <Button size="sm" onClick={nextStep}>
              {isLastStep ? "فهمت!" : "التالي"}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
