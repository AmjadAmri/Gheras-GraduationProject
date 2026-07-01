export interface Story {
  id: number;
  title: string;
  childId: number;
  childName: string;
  coverUrl: string;
  storyType: string;
  artStyle: string;
  targetBehavior: string;
  customBehavior?: string;
  status: string;
  pages: StoryPage[];

  // ✅ PDF fields
  pdfStatus?: "pending" | "generating" | "ready" | "failed";
  pdfProgress?: number;
  pdfError?: string;
  pdfReady?: boolean;
  pdfUrl?: string;

  createdAt: string;
}

export interface StoryPage {
  pageNumber: number;
  narrationText: string;
  illustrationUrl: string;
  audioUrl: string;
}

export interface StoryGenerationProgress {
  id: number;
  status: string;
  stage: string;
  message: string;
  title: string;
  totalPages: number;
  pagesWithImages: number;
  pagesWithAudio: number;
  initialPagesTarget: number;
  coverReady: boolean;

  // ✅ PDF fields أثناء التوليد
  pdfStatus?: "pending" | "generating" | "ready" | "failed";
  pdfProgress?: number;
  pdfError?: string;
  pdfReady?: boolean;
  pdfUrl?: string;
}

export interface StoryType {
  id: number;
  key: string;
  label: string;
  icon: string;
  description: string;
}

export interface ArtStyle {
  id: number;
  key: string;
  label: string;
  previewUrl: string;
  description: string;
}

export interface Behavior {
  id: number;
  key: string;
  label: string;
  icon: string;
  description: string;
}

export interface ConfigResponse {
  behaviors: Behavior[];
  genres: StoryType[];
  styles: ArtStyle[];
}

export interface ReadingLog {
  id: number;
  childId: number;
  storyId: number;
  storyTitle: string;
  timeSpent: number;
  startedAt: string;
  finishedAt: string | null;
}

export interface DashboardStats {
  totalStories: number;
  childrenCount: number;
  storiesRead: number;
  tasksCompleted: number;
  streak: number;
  radarData: { behavior: string; key: string; count: number }[];
  weeklyData: { day: string; stories: number }[];
}