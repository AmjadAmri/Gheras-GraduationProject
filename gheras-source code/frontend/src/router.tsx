import { createBrowserRouter } from "react-router-dom";
import { AuthLayout } from "./layouts/AuthLayout";
import { DashboardLayout } from "./layouts/DashboardLayout";
import { SignInPage } from "./pages/auth/SignInPage";
import { SignUpPage } from "./pages/auth/SignUpPage";
import { DashboardPage } from "./pages/dashboard/DashboardPage";
import { ChildrenListPage } from "./pages/children/ChildrenListPage";
import { AddChildPage } from "./pages/children/AddChildPage";
import { CreateStoryPage } from "./pages/stories/CreateStoryPage";
import { StoryGeneratingPage } from "./pages/stories/StoryGeneratingPage";
import { StoryViewerPage } from "./pages/stories/StoryViewerPage";
import { LibraryPage } from "./pages/library/LibraryPage";
import { ProgressPage } from "./pages/progress/ProgressPage";

export const router = createBrowserRouter([
  {
    path: "/auth",
    element: <AuthLayout />,
    children: [
      { path: "sign-in", element: <SignInPage /> },
      { path: "sign-up", element: <SignUpPage /> },
    ],
  },
  {
    path: "/",
    element: <DashboardLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "children", element: <ChildrenListPage /> },
      { path: "children/add", element: <AddChildPage /> },
      { path: "children/:id/edit", element: <AddChildPage /> },
      { path: "create-story", element: <CreateStoryPage /> },
      { path: "create-story/generating", element: <StoryGeneratingPage /> },
      { path: "stories/:storyId", element: <StoryViewerPage /> },
      { path: "library", element: <LibraryPage /> },
      { path: "progress", element: <ProgressPage /> },
    ],
  },
]);
