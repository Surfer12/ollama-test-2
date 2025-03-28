import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class ThinkToolTest {
    private Log<Thought> log;

    @BeforeEach
    void setUp() {
        log = new Log<>();
    }

    @Test
    void testThink() {
        // Given
        String thought1 = "This is a complex thought that requires reasoning.";
        String thought2 = "This is another thought that builds on the previous one.";
        // When
        log.think(new Thought(thought1));
        log.think(new Thought(thought2));
        // Then
        assertEquals(2, log.getLog().size());
        assertTrue(log.getLog().contains(new Thought(thought1)));
        assertTrue(log.getLog().contains(new Thought(thought2)));
    }

    @Test
    void testCompareTo() {
        // Given
        Thought thought1 = new Thought("This is a complex thought that requires reasoning.");
        Thought thought2 = new Thought("This is another thought that builds on the previous one.");
        // When
        int comparison = thought1.compareTo(thought2);
        // Then
        assertTrue(comparison < 0);
    }
}
