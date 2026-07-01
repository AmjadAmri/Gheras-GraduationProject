import { Link } from "react-router-dom";
import { cn } from "../lib/cn";
import { BookOpen, Image as ImageIcon } from "lucide-react";
import type { Story } from "../types/story";

interface StoryCardProps {
  story: Story;
  className?: string;
}

export function StoryCard({ story, className }: StoryCardProps) {
  const poster =
    story.coverUrl ||
    story.pages?.find((page) => page.illustrationUrl)?.illustrationUrl ||
    "";

  return (
    <Link
      to={`/stories/${story.id}`}
      className={cn(
        "group block rounded-xl bg-white border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow",
        className
      )}
    >
      <div className="aspect-[3/4] overflow-hidden bg-gray-100">
        {poster ? (
          <img
            src={poster}
            alt={story.title}
            className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-teal-500 to-cyan-600 text-white">
            <ImageIcon className="h-12 w-12 opacity-90" />
          </div>
        )}
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-gray-900 line-clamp-1">{story.title}</h3>
        <p className="text-sm text-gray-500 mt-1">{story.childName}</p>
        <div className="flex items-center gap-1.5 mt-2 text-xs text-gray-400">
          <BookOpen className="h-3.5 w-3.5" />
          <span>{story.pages.length} صفحات</span>
          <span className="mx-1">·</span>
          <span>{story.createdAt}</span>
        </div>
      </div>
    </Link>
  );
}
