import { useState, useCallback } from "react";
import type { WizardStep } from "../types/wizard";

export function useMultiStepForm(totalSteps: number = 3) {
  const [currentStep, setCurrentStep] = useState<WizardStep>(0);

  const next = useCallback(() => {
    setCurrentStep((prev) => Math.min(prev + 1, totalSteps - 1) as WizardStep);
  }, [totalSteps]);

  const back = useCallback(() => {
    setCurrentStep((prev) => Math.max(prev - 1, 0) as WizardStep);
  }, []);

  const goTo = useCallback((step: WizardStep) => {
    setCurrentStep(step);
  }, []);

  const reset = useCallback(() => {
    setCurrentStep(0);
  }, []);

  return {
    currentStep,
    next,
    back,
    goTo,
    reset,
    isFirst: currentStep === 0,
    isLast: currentStep === totalSteps - 1,
  };
}
