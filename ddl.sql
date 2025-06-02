CREATE TABLE usecase_phase_prompt_link (
    type VARCHAR(20) NOT NULL, -- 'exp', 'pp', 'prod'
    usecase_id BIGINT NOT NULL,
    prompt_history_id BIGINT NOT NULL,
    created_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
 
    CONSTRAINT pk_usecase_phase_prompt PRIMARY KEY (type, usecase_id),
 
    CONSTRAINT fk_usecase_link
        FOREIGN KEY (usecase_id)
        REFERENCES genai_usecase (usecase_id)
        ON DELETE CASCADE,
 
    CONSTRAINT fk_prompt_history
        FOREIGN KEY (prompt_history_id)
        REFERENCES genai_prompt_history (id)
        ON DELETE CASCADE
);
 
 
 
 
CREATE TABLE genai_prompt_history (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    usecase_id BIGINT NOT NULL,
    prompt TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255),
    created_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
 
    CONSTRAINT fk_usecase
        FOREIGN KEY (usecase_id)
        REFERENCES genai_usecase (usecase_id)
        ON DELETE CASCADE
);
