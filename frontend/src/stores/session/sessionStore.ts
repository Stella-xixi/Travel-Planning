import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { SessionInfo } from '@/types';
import { apiService } from '@/services/api';

interface SessionState {
  // 当前会话
  currentSessionId: string | null;

  // 会话列表
  sessions: SessionInfo[];
  loading: boolean;

  // Actions
  setCurrentSessionId: (id: string | null) => void;
  createSession: () => Promise<string>;
  deleteSession: (sessionId: string) => Promise<void>;
  updateSessionName: (sessionId: string, name: string) => Promise<void>;
  clearChat: (sessionId: string) => Promise<void>;
  refreshSessions: (includeEmpty?: boolean) => Promise<void>;
  switchSession: (sessionId: string | null) => Promise<void>;
}

export const useSessionStore = create<SessionState>()(
  devtools(
    (set, get) => ({
      currentSessionId: null,
      sessions: [],
      loading: false,

      setCurrentSessionId: (id) =>
        set({ currentSessionId: id }, false, 'session/setCurrentSessionId'),

      createSession: async () => {
        set({ loading: true }, false, 'session/createSession/start');
        try {
          const data = await apiService.createSession();
          await get().refreshSessions();
          set({ loading: false }, false, 'session/createSession/success');
          return data.session_id;
        } catch (error) {
          set({ loading: false }, false, 'session/createSession/error');
          throw error;
        }
      },

      deleteSession: async (sessionId) => {
        await apiService.deleteSession(sessionId);
        const { currentSessionId, refreshSessions } = get();

        if (sessionId === currentSessionId) {
          set({ currentSessionId: null }, false, 'session/deleteSession/clearCurrent');
        }

        await refreshSessions();
      },

      updateSessionName: async (sessionId, name) => {
        await apiService.updateSessionName(sessionId, name);
        await get().refreshSessions();
      },

      clearChat: async (sessionId) => {
        await apiService.clearChat(sessionId);
      },

      refreshSessions: async (includeEmpty = false) => {
        set({ loading: true }, false, 'session/refreshSessions/start');
        try {
          const data = await apiService.getSessions();
          const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);

          const uniqueSessionsMap = new Map(
            data.sessions.map((s) => [s.session_id, s])
          );
          const uniqueSessions = Array.from(uniqueSessionsMap.values());

          const activeSessions = includeEmpty
            ? uniqueSessions
            : uniqueSessions.filter(
                (s) =>
                  s.message_count > 0 || new Date(s.last_active) > oneHourAgo
              );

          set({ sessions: activeSessions, loading: false }, false, 'session/refreshSessions/success');
        } catch (error) {
          set({ loading: false }, false, 'session/refreshSessions/error');
        }
      },

      switchSession: async (sessionId) => {
        const { currentSessionId } = get();

        if (currentSessionId && sessionId !== currentSessionId) {
          // Save current session messages to cache
        }

        set({ currentSessionId: sessionId }, false, 'session/switchSession');
      },
    }),
    { name: 'SessionStore' }
  )
);
