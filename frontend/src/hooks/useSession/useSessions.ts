import { useCallback } from 'react';
import { useSessionStore } from '@/stores/session';

export const useSessions = () => {
  const { sessions, loading, currentSessionId, refreshSessions } = useSessionStore();

  return {
    sessions,
    loading,
    currentSessionId,
    refreshSessions,
  };
};

export const useSessionActions = () => {
  const {
    createSession,
    deleteSession,
    updateSessionName,
    clearChat,
    switchSession,
    setCurrentSessionId,
  } = useSessionStore();

  return {
    createSession: useCallback(async () => {
      return await createSession();
    }, [createSession]),

    deleteSession: useCallback(
      async (sessionId: string) => {
        await deleteSession(sessionId);
      },
      [deleteSession]
    ),

    updateSessionName: useCallback(
      async (sessionId: string, name: string) => {
        await updateSessionName(sessionId, name);
      },
      [updateSessionName]
    ),

    clearChat: useCallback(
      async (sessionId: string) => {
        await clearChat(sessionId);
      },
      [clearChat]
    ),

    switchSession: useCallback(
      async (sessionId: string | null) => {
        await switchSession(sessionId);
      },
      [switchSession]
    ),

    setCurrentSessionId: useCallback((id: string | null) => {
      setCurrentSessionId(id);
    }, []),
  };
};
