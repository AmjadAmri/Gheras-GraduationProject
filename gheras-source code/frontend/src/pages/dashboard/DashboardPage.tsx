import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useChildren } from "../../context/ChildrenContext";
import { api } from "../../lib/api";
import type { DashboardStats, Story } from "../../types/story";
import { StoryCard } from "../../components/StoryCard";
import { PageHeader } from "../../components/PageHeader";
import { StatCard } from "../../components/StatCard";
import { ChildCard } from "../../components/ChildCard";
import { Button } from "../../components/ui/Button";
import { BookOpen, Users, TrendingUp, CheckCircle, Plus } from "lucide-react";

export function DashboardPage() {
  const { user } = useAuth();
  const { children } = useChildren();
  const [stats, setStats] = useState<DashboardStats>({
    totalStories: 0,
    childrenCount: 0,
    storiesRead: 0,
    tasksCompleted: 0,
    streak: 0,
    radarData: [],
    weeklyData: [],
  });

  const [recentStories, setRecentStories] = useState<Story[]>([]);

  useEffect(() => {
    api.get<DashboardStats>("/stats/").then(setStats).catch(() => {});
    api.get<Story[]>("/stories/").then((data) => setRecentStories(data.slice(0, 4))).catch(() => {});
  }, []);

  return (
    <div>
      <PageHeader
        title={`مرحباً ${user?.name} 👋`}
        description="إليك ملخص نشاطك اليوم"
      />

      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-8">
        <StatCard
          label="إجمالي القصص"
          value={stats.totalStories}
          icon={BookOpen}
          color="text-emerald-600"
          bgColor="bg-emerald-100"
        />
        <StatCard
          label="قصص تمت قراءتها"
          value={stats.storiesRead}
          icon={CheckCircle}
          color="text-blue-600"
          bgColor="bg-blue-100"
        />
        <StatCard
          label="عدد الأطفال"
          value={children.length}
          icon={Users}
          color="text-sidebar"
          bgColor="bg-accent-gold/20"
        />
        <StatCard
          label="أيام متتالية"
          value={stats.streak}
          icon={TrendingUp}
          color="text-amber-600"
          bgColor="bg-amber-100"
        />
      </div>
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">أطفالي</h2>
          <Link to="/children">
            <Button variant="ghost" size="sm">
              عرض الكل
            </Button>
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {children.slice(0, 3).map((child) => (
            <ChildCard key={child.id} child={child} />
          ))}
          {children.length === 0 && (
            <Link
              to="/children/add"
              className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-gray-300 bg-white p-8 text-center hover:border-primary hover:bg-emerald-50/30 transition-colors"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
                <Plus className="h-6 w-6 text-gray-400" />
              </div>
              <span className="text-sm font-medium text-gray-600">
                إضافة طفل
              </span>
            </Link>
          )}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">القصص الأخيرة</h2>
          <Link to="/library">
            <Button variant="ghost" size="sm">
              عرض الكل
            </Button>
          </Link>
        </div>
        {recentStories.length === 0 ? (
          <div className="rounded-xl border-2 border-dashed border-gray-200 bg-white p-12 text-center">
            <BookOpen className="h-10 w-10 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">لم تُنشئ أي قصص بعد</p>
            <Link to="/create-story">
              <Button variant="ghost" size="sm" className="mt-2">
                إنشاء قصة جديدة
              </Button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {recentStories.map((story) => (
              <StoryCard key={story.id} story={story} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
