from utils.models import get_model


def generate_variation(phrase, initial=True, base_lang="English"):
    if initial:
        system_instruction = f"""You are an assistant that generates translations for language learning purposes, by translating an input phrase to {base_lang}. If the input is already in {base_lang}, just respond with the same phrase."""
    else:
        system_instruction = f"""You are an assistant that generates augmented translations for language learning. Translate and augment input phrases to {base_lang}. If the input is already in {base_lang}, just provide a slight variation in {base_lang}.

        ### Task:
        Given an input phrase, translate it to {base_lang} with slight augmentation. Follow these rules:
        1. **Preserve key nouns and verbs** for effective practice.
        2. **Introduce grammatical variations** such as:
        - Changing pronouns (e.g., 'he' → 'she').
        - Slightly adjusting sentence structure (e.g., 'He went home quickly' → 'Quickly, he went home.').
        3. **Retain all nuances**, such as gender, tone, or formality. Add details if needed (e.g., use names to clarify gender).
        4. Keep the translation **at the same difficulty level** as the original.
        5. Provide **one {base_lang} translation only**.

        ### Example:
        - **Input Phrase**: Soy arquitecta.
        - **Translation**: I am Rebecca, an architect."""

    model = get_model("openai")
    user_instruction = f'Input Phrase: "{phrase}"\nAugmented Translation:'

    try:
        response = model.generate_response(
            system_prompt=system_instruction,
            user_prompt=user_instruction,
            model_name="gpt-4o-mini",
        )
        return response

    except Exception as e:
        print(f"Error generating variation: {e}")
        return None


if __name__ == "__main__":
    input_phrase = "Frida Kahlo y Diego Rivera se casaron en 1929 y después en 1940."
    variation = generate_variation(input_phrase, initial=True)
    if variation:
        print(f"Original: {input_phrase}")
        print(f"Variation: {variation}")
