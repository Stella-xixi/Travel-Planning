import { useCallback } from 'react';
import { useConfigStore } from '@/stores/config';

export const useAvailableModels = () => {
  const { availableModels, loadingModels, loadModels } = useConfigStore();

  return {
    models: availableModels,
    loading: loadingModels,
    loadModels,
  };
};

export const useModelSwitch = () => {
  const { currentModelId, setCurrentModelId } = useConfigStore();

  return {
    currentModelId,
    setModel: useCallback(
      async (modelId: string) => {
        await setCurrentModelId(modelId);
      },
      [setCurrentModelId]
    ),
  };
};
